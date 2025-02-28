import React, { useState } from "react";

type FileUploadProps = {
  onFileSelect: (file: File) => void;
};

const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      const file = event.target.files[0];
      setSelectedFile(file);
      onFileSelect(file);
    }
  };

  return (
    <div>
      <input type="file" accept=".pdf,.docx" onChange={handleFileChange} />
      {selectedFile && <p>Selected File: {selectedFile.name}</p>}
    </div>
  );
};

export default FileUpload;
