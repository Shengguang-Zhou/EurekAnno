import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Divider,
  Stack,
  Alert,
  Snackbar,
  LinearProgress,
  useTheme
} from '@mui/material';
import BrushIcon from '@mui/icons-material/Brush';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import SearchIcon from '@mui/icons-material/Search';
import { useApp } from '../context/AppContext';
import yoloeApi from '../api/yoloeApi';

const ImagePromptPanel = () => {
  const theme = useTheme();
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');
  
  const { 
    imagePrompts, 
    updateImagePrompts, 
    currentImage,
    isLoading,
    setIsLoading,
    setError,
    addDetectionResult
  } = useApp();
  
  const handleClearPrompts = () => {
    updateImagePrompts([], []);
  };
  
  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };
  
  const showSnackbar = (message, severity = 'success') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };
  
  const handleDetection = async () => {
    if (!currentImage) return;
    
    try {
      if (imagePrompts.bboxes.length === 0) {
        showSnackbar('Please draw at least one bounding box', 'warning');
        return;
      }
      
      setIsLoading(true);
      setError(null);
      
      const response = await yoloeApi.imagePromptInference(
        currentImage.file, 
        imagePrompts.bboxes, 
        imagePrompts.cls
      );
      
      // Store result - Extract the actual results object
      if (response && response.results) {
        addDetectionResult(currentImage.id, response.results);
        showSnackbar('Detection completed successfully');
      } else {
        console.error('Invalid response structure:', response);
        showSnackbar('Detection completed, but results structure is invalid.', 'warning');
      }
      
    } catch (error) {
      console.error('Detection error:', error);
      const errorMessage = error.response?.status === 400 
        ? 'Model not found or configuration error. Please check server logs.'
        : error.message || 'Error during detection';
      
      setError(errorMessage);
      showSnackbar(`Error: ${errorMessage}`, 'error');
      
      if (currentImage && imagePrompts && imagePrompts.bboxes && imagePrompts.bboxes.length > 0) {
        addDetectionResult(currentImage.id, { 
          classes: ['Object'], 
          objects: [] 
        });
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        height: '100%',
        borderRadius: 2,
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
        Image Prompts
      </Typography>
      
      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
        Draw bounding boxes on the image to define regions for object detection.
      </Typography>
      
      <Alert severity="info" sx={{ mb: 2 }}>
        Click and drag on the image to draw bounding boxes
      </Alert>
      
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" color="textSecondary" gutterBottom>
          {imagePrompts.bboxes.length > 0 
            ? `Drawn boxes: ${imagePrompts.bboxes.length}` 
            : 'No boxes drawn yet'}
        </Typography>
        
        {imagePrompts.bboxes.length > 0 && (
          <Stack spacing={1}>
            {imagePrompts.bboxes.map((bbox, index) => (
              <Box 
                key={index}
                sx={{
                  p: 1,
                  border: '1px solid',
                  borderColor: 'neutral.200',
                  borderRadius: 1,
                  bgcolor: 'background.paper'
                }}
              >
                <Typography variant="caption" color="textSecondary">
                  Box {index + 1}: {Math.round(bbox[0] * 100)}%, {Math.round(bbox[1] * 100)}% to {Math.round(bbox[2] * 100)}%, {Math.round(bbox[3] * 100)}%
                </Typography>
              </Box>
            ))}
          </Stack>
        )}
      </Box>
      
      <Box sx={{ flexGrow: 1 }} />
      
      <Box sx={{ mt: 'auto' }}>
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Button
            variant="outlined"
            color="primary"
            startIcon={<DeleteSweepIcon />}
            onClick={handleClearPrompts}
            disabled={imagePrompts.bboxes.length === 0 || !currentImage}
            size="small"
          >
            Clear All Boxes
          </Button>
          
          <Button
            variant="contained"
            color="primary"
            startIcon={<SearchIcon />}
            onClick={handleDetection}
            disabled={isLoading || !currentImage || imagePrompts.bboxes.length === 0}
            fullWidth
          >
            {isLoading ? 'Detecting...' : 'Detect Objects'}
          </Button>
        </Stack>
        
        {isLoading && (
          <LinearProgress 
            color="primary" 
            sx={{ 
              height: 6, 
              borderRadius: 3,
              mb: 2 
            }} 
          />
        )}
      </Box>
      
      <Box sx={{ p: 2, bgcolor: 'primary.light', color: 'white', borderRadius: 1, opacity: 0.9 }}>
        <Stack direction="row" spacing={1} alignItems="center">
          <BrushIcon fontSize="small" />
          <Typography variant="body2" fontWeight="medium">
            Drawing Mode Active
          </Typography>
        </Stack>
      </Box>
      
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbarSeverity} 
          elevation={6}
          variant="filled"
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Paper>
  );
};

export default ImagePromptPanel;  