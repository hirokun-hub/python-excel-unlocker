import React from "react";

// ファイルアップロードコンポーネントのPropsの型定義
interface FileUploadProps {
  onFilesAdded: (files: File[]) => void; // ファイルが追加されたときに呼び出されるコールバック関数
}

/**
 * ファイル選択ボタンとドラッグ＆ドロップエリアを提供するコンポーネント
 * @param {FileUploadProps} props - コンポーネントのプロパティ
 */
const FileUpload: React.FC<FileUploadProps> = ({ onFilesAdded }) => {
  // ドラッグオーバーイベントのハンドラ
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault(); // デフォルトの動作（ファイルを開くなど）を防ぐ
    e.stopPropagation();
  };

  // ドロップイベントのハンドラ
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault(); // デフォルトの動作を防ぐ
    e.stopPropagation();

    const files = Array.from(e.dataTransfer.files); // ドロップされたファイルを取得
    if (files && files.length > 0) {
      onFilesAdded(files); // 親コンポーネントにファイルを渡す
    }
  };

  // ファイル選択ダイアログからのファイル選択イベントのハンドラ
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []); // 選択されたファイルを取得
    if (files && files.length > 0) {
      onFilesAdded(files); // 親コンポーネントにファイルを渡す
    }
  };

  return (
    <div
      className="w-full box-border p-8 border-2 border-dashed border-gray-300 rounded-lg text-center cursor-pointer hover:border-blue-500 transition-colors"
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={() => document.getElementById("fileInput")?.click()} // divクリックでファイル入力をトリガー
    >
      <input
        type="file"
        id="fileInput"
        multiple // 複数ファイルの選択を許可
        className="hidden" // input要素は非表示にする
        onChange={handleFileChange}
        accept=".xlsx, .xls" // Excelファイルのみを許可
      />
      <p className="text-gray-500">
        ここにファイルをドラッグ＆ドロップするか、クリックしてファイルを選択してください
      </p>
      <p className="text-sm text-gray-400 mt-2">(対応ファイル: .xlsx, .xls)</p>
    </div>
  );
};

export default FileUpload;
