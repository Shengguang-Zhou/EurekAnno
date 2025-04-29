import React, { useRef, useState } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Paper, 
  Stack,
  useTheme
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import InsertPhotoIcon from '@mui/icons-material/InsertPhoto';
import { useApp } from '../context/AppContext';

const ImageUploader = () => {
  const theme = useTheme();
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const { addImage } = useApp();
  
  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFiles(files);
    }
  };
  
  const handleFiles = (files) => {
    Array.from(files).forEach(file => {
      if (file.type.match('image.*')) {
        addImage(file);
      }
    });
    
    // Reset the input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFiles(files);
    }
  };
  
  const handleClick = () => {
    fileInputRef.current?.click();
  };
  
  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        bgcolor: isDragging ? 'rgba(238, 76, 44, 0.04)' : 'background.paper',
        border: '2px dashed',
        borderColor: isDragging ? 'primary.main' : 'neutral.300',
        borderRadius: 2,
        transition: 'all 0.2s ease-in-out',
        cursor: 'pointer',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center'
      }}
      onClick={handleClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        accept="image/*"
        type="file"
        multiple
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />
      
      <Stack spacing={2} alignItems="center">
        <Box 
          sx={{
            width: 80,
            height: 80,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '50%',
            bgcolor: 'rgba(238, 76, 44, 0.08)',
            mb: 2
          }}
        >
          <CloudUploadIcon 
            sx={{ 
              fontSize: 40, 
              color: 'primary.main' 
            }} 
          />
        </Box>
        
        <Typography variant="h6" color="textPrimary" textAlign="center">
          Drag and drop images
        </Typography>
        
        <Typography variant="body2" color="textSecondary" textAlign="center">
          or click to browse files
        </Typography>
        
        <Button
          variant="contained"
          color="primary"
          startIcon={<InsertPhotoIcon />}
          onClick={(e) => {
            e.stopPropagation();
            handleClick();
          }}
          sx={{ mt: 2 }}
        >
          Upload Images
        </Button>
        
        <Typography variant="caption" color="textSecondary" textAlign="center">
          Supported formats: JPG, PNG, JPEG
        </Typography>
      </Stack>
    </Paper>
  );
};

export default ImageUploader; 