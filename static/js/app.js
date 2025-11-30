/**
 * Excel Unlocker クライアントサイド JavaScript
 * 
 * 機能:
 * - 並列リクエスト処理（Promise.all + 同時実行数制限）
 * - 各ファイルの進捗表示（待機中/処理中/完了/エラー）
 * - 429 受信時のリトライロジック
 * - 解除成功時のダウンロードリンク表示
 * 
 * Requirements: 2.3, 2.4, 2.5, 2.6
 */

(function() {
    'use strict';

    // 設定値（HTMLから注入）
    const CONFIG = window.APP_CONFIG || {
        clientConcurrency: 3,
        maxFileSizeMB: 50,
        allowedExtensions: ['.xlsx', '.xls'],
        maxRetryCount: 3
    };

    // 状態管理
    const state = {
        selectedFiles: [],
        isProcessing: false
    };

    // DOM要素のキャッシュ
    const elements = {};

    /**
     * 初期化処理
     */
    function init() {
        cacheElements();
        bindEvents();
        console.log('Excel Unlocker initialized', CONFIG);
    }

    /**
     * DOM要素をキャッシュ
     */
    function cacheElements() {
        elements.dropZone = document.getElementById('drop-zone');
        elements.fileInput = document.getElementById('file-input');
        elements.fileListSection = document.getElementById('file-list-section');
        elements.fileList = document.getElementById('file-list');
        elements.clearFilesBtn = document.getElementById('clear-files-btn');
        elements.unlockForm = document.getElementById('unlock-form');
        elements.password1 = document.getElementById('password1');
        elements.password2 = document.getElementById('password2');
        elements.unlockBtn = document.getElementById('unlock-btn');
        elements.resultsSection = document.getElementById('results-section');
        elements.resultsList = document.getElementById('results-list');
    }

    /**
     * イベントリスナーをバインド
     */
    function bindEvents() {
        // ドラッグ＆ドロップ
        elements.dropZone.addEventListener('dragover', handleDragOver);
        elements.dropZone.addEventListener('dragleave', handleDragLeave);
        elements.dropZone.addEventListener('drop', handleDrop);

        // ファイル選択
        elements.fileInput.addEventListener('change', handleFileSelect);

        // ファイルクリア
        elements.clearFilesBtn.addEventListener('click', clearFiles);

        // フォーム送信
        elements.unlockForm.addEventListener('submit', handleSubmit);

        // パスワード表示切替
        document.querySelectorAll('.toggle-password').forEach(btn => {
            btn.addEventListener('click', togglePasswordVisibility);
        });

        // 入力変更時のボタン状態更新
        elements.password1.addEventListener('input', updateUnlockButtonState);
    }


    // ========================================
    // ドラッグ＆ドロップ処理
    // ========================================

    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.dropZone.classList.add('drag-over');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.dropZone.classList.remove('drag-over');
    }

    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.dropZone.classList.remove('drag-over');

        const files = Array.from(e.dataTransfer.files);
        addFiles(files);
    }

    // ========================================
    // ファイル選択処理
    // ========================================

    function handleFileSelect(e) {
        const files = Array.from(e.target.files);
        addFiles(files);
        // 同じファイルを再選択できるようにリセット
        e.target.value = '';
    }

    /**
     * ファイルを追加（バリデーション付き）
     */
    function addFiles(files) {
        const validFiles = files.filter(file => validateFile(file));
        
        if (validFiles.length === 0) return;

        state.selectedFiles = [...state.selectedFiles, ...validFiles];
        renderFileList();
        updateUnlockButtonState();
    }

    /**
     * ファイルバリデーション
     */
    function validateFile(file) {
        // 拡張子チェック
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!CONFIG.allowedExtensions.includes(ext)) {
            showNotification(`${file.name}: サポートされていないファイル形式です`, 'error');
            return false;
        }

        // サイズチェック
        const maxBytes = CONFIG.maxFileSizeMB * 1024 * 1024;
        if (file.size > maxBytes) {
            showNotification(`${file.name}: ファイルサイズが大きすぎます（上限: ${CONFIG.maxFileSizeMB}MB）`, 'error');
            return false;
        }

        // 重複チェック
        if (state.selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
            showNotification(`${file.name}: 既に選択されています`, 'warning');
            return false;
        }

        return true;
    }

    /**
     * ファイル一覧を描画
     */
    function renderFileList() {
        if (state.selectedFiles.length === 0) {
            elements.fileListSection.classList.add('hidden');
            return;
        }

        elements.fileListSection.classList.remove('hidden');
        elements.fileList.innerHTML = state.selectedFiles.map((file, index) => `
            <li class="file-item" data-index="${index}">
                <span class="file-name">${escapeHtml(file.name)}</span>
                <span class="file-size">${formatFileSize(file.size)}</span>
                <button type="button" class="remove-file-btn" data-index="${index}" aria-label="削除">×</button>
            </li>
        `).join('');

        // 削除ボタンのイベント
        elements.fileList.querySelectorAll('.remove-file-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index, 10);
                removeFile(index);
            });
        });
    }

    /**
     * ファイルを削除
     */
    function removeFile(index) {
        state.selectedFiles.splice(index, 1);
        renderFileList();
        updateUnlockButtonState();
    }

    /**
     * 全ファイルをクリア
     */
    function clearFiles() {
        state.selectedFiles = [];
        renderFileList();
        updateUnlockButtonState();
    }


    // ========================================
    // フォーム送信・解除処理
    // ========================================

    /**
     * フォーム送信ハンドラ
     */
    async function handleSubmit(e) {
        e.preventDefault();

        if (state.isProcessing || state.selectedFiles.length === 0) return;

        const password1 = elements.password1.value;
        const password2 = elements.password2.value;

        if (!password1) {
            showNotification('第1パスワードを入力してください', 'error');
            return;
        }

        state.isProcessing = true;
        setProcessingUI(true);
        showResultsSection();

        try {
            // 並列処理（同時実行数制限付き）
            await processFilesWithConcurrency(
                state.selectedFiles,
                password1,
                password2,
                CONFIG.clientConcurrency
            );
        } finally {
            state.isProcessing = false;
            setProcessingUI(false);
        }
    }

    /**
     * 同時実行数を制限した並列処理
     * @param {File[]} files - 処理対象ファイル
     * @param {string} password1 - 第1パスワード
     * @param {string} password2 - 第2パスワード
     * @param {number} concurrency - 同時実行数
     */
    async function processFilesWithConcurrency(files, password1, password2, concurrency) {
        // 結果リストを初期化（全ファイルを「待機中」で表示）
        initResultsList(files);

        const queue = [...files];
        const executing = new Set();

        while (queue.length > 0 || executing.size > 0) {
            // 同時実行数に達していなければ、キューから取り出して実行
            while (queue.length > 0 && executing.size < concurrency) {
                const file = queue.shift();
                const index = files.indexOf(file);
                
                const promise = processFile(file, index, password1, password2)
                    .finally(() => executing.delete(promise));
                
                executing.add(promise);
            }

            // 少なくとも1つの処理が完了するまで待機
            if (executing.size > 0) {
                await Promise.race(executing);
            }
        }
    }

    /**
     * 単一ファイルの解除処理（リトライ付き）
     */
    async function processFile(file, index, password1, password2, retryCount = 0) {
        updateResultItem(index, 'processing', '処理中...');

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('password1', password1);
            if (password2) {
                formData.append('password2', password2);
            }

            const response = await fetch('/unlock', {
                method: 'POST',
                body: formData
            });

            // 429 Too Many Requests の処理
            if (response.status === 429) {
                const data = await response.json();
                const retryAfter = data.retryAfter || 5;

                if (retryCount < CONFIG.maxRetryCount) {
                    updateResultItem(index, 'waiting', `混雑中... ${retryAfter}秒後にリトライ (${retryCount + 1}/${CONFIG.maxRetryCount})`);
                    await sleep(retryAfter * 1000);
                    return processFile(file, index, password1, password2, retryCount + 1);
                } else {
                    updateResultItem(index, 'error', 'サーバーが混雑しています。しばらく待ってから再試行してください。');
                    return;
                }
            }

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                updateResultItem(index, 'success', '解除成功', data.downloadUrl);
            } else {
                updateResultItem(index, 'error', data.message || 'エラーが発生しました');
            }
        } catch (error) {
            console.error('処理エラー:', error);
            updateResultItem(index, 'error', 'ネットワークエラーが発生しました');
        }
    }


    // ========================================
    // 結果表示
    // ========================================

    /**
     * 結果セクションを表示
     */
    function showResultsSection() {
        elements.resultsSection.classList.remove('hidden');
    }

    /**
     * 結果リストを初期化（全ファイルを待機中で表示）
     */
    function initResultsList(files) {
        elements.resultsList.innerHTML = files.map((file, index) => `
            <li class="result-item" data-index="${index}" data-status="waiting">
                <div class="result-info">
                    <span class="result-filename">${escapeHtml(file.name)}</span>
                    <span class="result-status">待機中...</span>
                </div>
                <div class="result-actions"></div>
            </li>
        `).join('');
    }

    /**
     * 結果アイテムを更新
     * @param {number} index - ファイルインデックス
     * @param {string} status - 状態（waiting/processing/success/error）
     * @param {string} message - 表示メッセージ
     * @param {string} [downloadUrl] - ダウンロードURL（成功時のみ）
     */
    function updateResultItem(index, status, message, downloadUrl = null) {
        const item = elements.resultsList.querySelector(`[data-index="${index}"]`);
        if (!item) return;

        item.dataset.status = status;
        
        const statusEl = item.querySelector('.result-status');
        statusEl.textContent = message;

        const actionsEl = item.querySelector('.result-actions');
        
        if (status === 'success' && downloadUrl) {
            // ダウンロードボタンを表示
            actionsEl.innerHTML = `
                <a href="${escapeHtml(downloadUrl)}" class="download-btn" download>
                    <svg class="download-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                    ダウンロード
                </a>
            `;
        } else if (status === 'processing') {
            actionsEl.innerHTML = `
                <span class="processing-spinner">
                    <svg class="spinner" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="31.4 31.4"/>
                    </svg>
                </span>
            `;
        } else {
            actionsEl.innerHTML = '';
        }
    }

    // ========================================
    // UI ヘルパー
    // ========================================

    /**
     * 処理中UIの切り替え
     */
    function setProcessingUI(isProcessing) {
        elements.unlockBtn.disabled = isProcessing;
        elements.unlockBtn.querySelector('.btn-text').classList.toggle('hidden', isProcessing);
        elements.unlockBtn.querySelector('.btn-loading').classList.toggle('hidden', !isProcessing);
        
        // フォーム入力を無効化
        elements.password1.disabled = isProcessing;
        elements.password2.disabled = isProcessing;
        elements.fileInput.disabled = isProcessing;
        elements.clearFilesBtn.disabled = isProcessing;
    }

    /**
     * 解除ボタンの状態を更新
     */
    function updateUnlockButtonState() {
        const hasFiles = state.selectedFiles.length > 0;
        const hasPassword = elements.password1.value.length > 0;
        elements.unlockBtn.disabled = !hasFiles || !hasPassword || state.isProcessing;
    }

    /**
     * パスワード表示切替
     */
    function togglePasswordVisibility(e) {
        const targetId = e.currentTarget.dataset.target;
        const input = document.getElementById(targetId);
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        e.currentTarget.classList.toggle('active', !isPassword);
    }

    /**
     * 通知を表示
     */
    function showNotification(message, type = 'info') {
        // シンプルなアラート（将来的にはトースト通知に置き換え可能）
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // 一時的な通知要素を作成
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        // アニメーション後に削除
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }


    // ========================================
    // ユーティリティ関数
    // ========================================

    /**
     * HTMLエスケープ
     */
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * ファイルサイズをフォーマット
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    /**
     * スリープ関数
     */
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ========================================
    // 初期化実行
    // ========================================

    // DOMContentLoaded で初期化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
