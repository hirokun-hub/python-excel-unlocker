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
     * 単一ファイルの解除処理（リトライ付き + アップロード進捗表示）
     */
    async function processFile(file, index, password1, password2, retryCount = 0) {
        updateResultItem(index, 'uploading', 'アップロード中...');
        updateProgress(index, 0, 'upload');

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('password1', password1);
            if (password2) {
                formData.append('password2', password2);
            }

            // XMLHttpRequestでアップロード進捗を取得
            const result = await uploadWithProgress(formData, index);

            // 429 Too Many Requests の処理
            if (result.status === 429) {
                const data = result.data;
                const retryAfter = data.retryAfter || 5;

                if (retryCount < CONFIG.maxRetryCount) {
                    updateResultItem(index, 'waiting', `混雑中... ${retryAfter}秒後にリトライ`);
                    updateProgress(index, 0, 'upload');
                    await sleep(retryAfter * 1000);
                    return processFile(file, index, password1, password2, retryCount + 1);
                } else {
                    updateResultItem(index, 'error', 'サーバーが混雑しています');
                    return;
                }
            }

            const data = result.data;

            if (result.status >= 200 && result.status < 300 && data.status === 'success') {
                updateResultItem(index, 'success', '解除成功', data.downloadUrl);
            } else {
                updateResultItem(index, 'error', data.message || 'エラーが発生しました');
            }
        } catch (error) {
            console.error('処理エラー:', error);
            updateResultItem(index, 'error', 'ネットワークエラーが発生しました');
        }
    }

    /**
     * XMLHttpRequestでアップロード（進捗表示付き）
     * @param {FormData} formData - 送信データ
     * @param {number} index - ファイルインデックス
     * @returns {Promise<{status: number, data: object}>}
     */
    function uploadWithProgress(formData, index) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // アップロード進捗イベント
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    // アップロードは0-50%の範囲で表示
                    const percent = (e.loaded / e.total) * 50;
                    updateProgress(index, percent, 'upload');
                }
            });

            // アップロード完了 → 処理中へ
            xhr.upload.addEventListener('load', () => {
                updateResultItem(index, 'processing', '解除処理中...');
                updateProgress(index, 50, 'processing');
            });

            // レスポンス受信完了
            xhr.addEventListener('load', () => {
                try {
                    const data = JSON.parse(xhr.responseText);
                    resolve({ status: xhr.status, data });
                } catch (e) {
                    reject(new Error('レスポンスの解析に失敗しました'));
                }
            });

            // エラー
            xhr.addEventListener('error', () => {
                reject(new Error('ネットワークエラー'));
            });

            xhr.addEventListener('abort', () => {
                reject(new Error('リクエストが中断されました'));
            });

            xhr.open('POST', '/unlock');
            xhr.send(formData);
        });
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
     * 結果リストを初期化（全ファイルを待機中で表示 + 進捗バー付き）
     */
    function initResultsList(files) {
        elements.resultsList.innerHTML = files.map((file, index) => `
            <li class="result-item" data-index="${index}" data-status="waiting">
                <div class="result-header">
                    <span class="result-filename">${escapeHtml(file.name)}</span>
                    <span class="result-size">${formatFileSize(file.size)}</span>
                </div>
                <div class="result-progress-container">
                    <div class="result-progress-bar">
                        <div class="result-progress-fill" style="width: 0%"></div>
                    </div>
                    <span class="result-progress-text">0%</span>
                </div>
                <div class="result-status-row">
                    <span class="result-status-icon"></span>
                    <span class="result-status">待機中</span>
                </div>
                <div class="result-actions"></div>
            </li>
        `).join('');
    }

    /**
     * 進捗バーを更新
     * @param {number} index - ファイルインデックス
     * @param {number} percent - 進捗率（0-100）
     * @param {string} phase - フェーズ（upload/processing/complete）
     */
    function updateProgress(index, percent, phase = 'upload') {
        const item = elements.resultsList.querySelector(`[data-index="${index}"]`);
        if (!item) return;

        const progressFill = item.querySelector('.result-progress-fill');
        const progressText = item.querySelector('.result-progress-text');
        
        progressFill.style.width = `${percent}%`;
        progressFill.dataset.phase = phase;
        
        if (phase === 'upload') {
            progressText.textContent = `アップロード ${Math.round(percent)}%`;
        } else if (phase === 'processing') {
            progressText.textContent = '解除処理中...';
            progressFill.classList.add('pulse');
        } else if (phase === 'complete') {
            progressText.textContent = '完了';
            progressFill.classList.remove('pulse');
        } else if (phase === 'error') {
            progressText.textContent = 'エラー';
            progressFill.classList.remove('pulse');
        }
    }

    /**
     * 結果アイテムを更新
     * @param {number} index - ファイルインデックス
     * @param {string} status - 状態（waiting/uploading/processing/success/error）
     * @param {string} message - 表示メッセージ
     * @param {string} [downloadUrl] - ダウンロードURL（成功時のみ）
     */
    function updateResultItem(index, status, message, downloadUrl = null) {
        const item = elements.resultsList.querySelector(`[data-index="${index}"]`);
        if (!item) return;

        item.dataset.status = status;
        
        const statusEl = item.querySelector('.result-status');
        const statusIconEl = item.querySelector('.result-status-icon');
        statusEl.textContent = message;

        // ステータスアイコンを更新
        const icons = {
            waiting: '⏳',
            uploading: '📤',
            processing: '⚙️',
            success: '✅',
            error: '❌'
        };
        statusIconEl.textContent = icons[status] || '';

        const actionsEl = item.querySelector('.result-actions');
        
        if (status === 'success' && downloadUrl) {
            // 進捗バーを完了状態に
            updateProgress(index, 100, 'complete');
            
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
        } else if (status === 'error') {
            // 進捗バーをエラー状態に
            updateProgress(index, 100, 'error');
            actionsEl.innerHTML = '';
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
