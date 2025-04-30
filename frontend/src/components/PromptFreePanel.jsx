import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Alert, 
  Divider,
  Stack,
  Button,
  LinearProgress,
  Snackbar,
  useTheme 
} from '@mui/material';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import SearchIcon from '@mui/icons-material/Search';
import { useApp } from '../context/AppContext';
import yoloeApi from '../api/yoloeApi';

const PromptFreePanel = () => {
  const theme = useTheme();
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');
  
  const { 
    currentImage,
    isLoading,
    setIsLoading,
    setError,
    addDetectionResult
  } = useApp();

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
      setIsLoading(true);
      setError(null);
      
      const response = await yoloeApi.promptFreeInference(currentImage.file);
      
      // Store result - Extract the actual results object
      if (response && response.results) {
        addDetectionResult(currentImage.id, response.results);
        showSnackbar('Detection completed successfully');
      } else {
        // Handle cases where results might be missing
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
      
      if (currentImage) {
        addDetectionResult(currentImage.id, { 
          classes: [], 
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
        Prompt-Free Mode
      </Typography>
      
      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
        Automatic object detection without any prompts. The model will detect all objects it can recognize in the image.
      </Typography>
      
      <Alert severity="info" sx={{ mb: 2 }}>
        Click the "Detect Objects" button to start automatic detection
      </Alert>
      
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
        <Box 
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 80,
            height: 80,
            borderRadius: '50%',
            bgcolor: 'rgba(238, 76, 44, 0.12)',
            mb: 2
          }}
        >
          <AutoFixHighIcon sx={{ fontSize: 40, color: 'primary.main' }} />
        </Box>
        
        <Typography variant="h6" color="primary.main" textAlign="center">
          Auto-Detection Ready
        </Typography>
        
        <Typography variant="body2" color="textSecondary" textAlign="center" sx={{ mt: 1, maxWidth: 280, mx: 'auto' }}>
          {currentImage 
            ? 'Click "Detect Objects" to automatically identify all objects in your image'
            : 'Upload an image to begin auto-detection'}
        </Typography>
      </Box>
      
      <Box sx={{ mt: 'auto', mb: 2 }}>
        <Button
          variant="contained"
          color="primary"
          fullWidth
          startIcon={<SearchIcon />}
          onClick={handleDetection}
          disabled={isLoading || !currentImage}
          sx={{ mt: 2 }}
        >
          {isLoading ? 'Detecting...' : 'Detect Objects'}
        </Button>
        
        {isLoading && (
          <LinearProgress 
            color="primary" 
            sx={{ 
              mt: 2,
              height: 6, 
              borderRadius: 3 
            }} 
          />
        )}
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

export default PromptFreePanel;  