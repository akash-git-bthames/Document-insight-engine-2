// DocumentUpload.jsx
import React, { useState } from "react";
import axios from "axios";
import NLPQuery from "./NLPQuery";
import Loader from "./Loaders";
import Loader1 from "./Loader1"
import TaskAltIcon from '@mui/icons-material/TaskAlt';

const DocumentUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [parsingStatus, setParsingStatus] = useState("");
  const [showLoader,setShowLoader]=useState(false);
  const [showLoader1,setShowLoader1]=useState(false);


  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus("Please select a file to upload");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      setUploadStatus("Uploading...");
      setShowLoader1(true)
      
      const response = await axios.post("http://65.2.86.51:8000/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setUploadStatus("Upload successful!");
      setShowLoader1(false);

      // Simulate a status check for parsing
      setShowLoader(true);
      setParsingStatus("Parsing in progress...");
      
      setTimeout(() => {setParsingStatus("Parsing completed!")
        setShowLoader(false);
      }, 3000);
    } catch (error) {
      setUploadStatus("Upload failed");
    }
  };

  return (
    <div>
      <div className="w-[60vw] m-auto flex flex-col items-center  gap-14 shadow-xl bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg mt-10 p-8">
      <h1 className="text-3xl font-bold text-white mt-10">Document Upload</h1>
      <div className="flex space-x-4">
        <input type="file" className="input" onChange={handleFileChange} />
        <button
          className="bg-white text-purple-500 px-6 py-2 rounded-lg shadow-md hover:bg-purple-500 hover:text-white transition-colors"
          onClick={handleUpload}
        >
          Upload
        </button>
      </div>
      <div className="text-white flex items-center ">
        <div>{showLoader1 && <Loader1/>}</div>
        <div className={`text-lg font-bold flex items-center gap-2 ${uploadStatus==="Upload successful!"? "text-green-600":""}`}>{uploadStatus==="Upload successful!"&&<TaskAltIcon/> } <div>{uploadStatus}</div></div>
        </div>
        
         {parsingStatus && <div className="text-white flex flex-col items-center gap-2 ">
          {showLoader && <Loader/>}
          {parsingStatus==="Parsing completed!"&& <div className="text-green-500"><TaskAltIcon/></div>}
          <div className={` ${parsingStatus==="Parsing completed!"?"text-green-500 text-xl font-bold":""}`}>{parsingStatus}</div>
          
          </div>}
          
       

          {parsingStatus==="Parsing completed!" && <NLPQuery />}
    </div>
   
    
    </div>
  );
};

export default DocumentUpload;
