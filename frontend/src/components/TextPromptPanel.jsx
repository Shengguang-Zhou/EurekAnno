import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Chip, 
  Stack, 
  IconButton, 
  Divider,
  Paper,
  LinearProgress,
  Alert,
  Snackbar
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';
import { useApp } from '../context/AppContext';
import yoloeApi from '../api/yoloeApi';

const TextPromptPanel = () => {
  const [inputValue, setInputValue] = useState('');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');
  
  const { 
    textPrompts, 
    addTextPrompt, 
    removeTextPrompt, 
    clearTextPrompts, 
    currentImage,
    isLoading,
    setIsLoading,
    setError,
    addDetectionResult
  } = useApp();
  
  const handleAddPrompt = () => {
    if (inputValue.trim() && !textPrompts.includes(inputValue.trim())) {
      addTextPrompt(inputValue.trim());
      setInputValue('');
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddPrompt();
    }
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
      if (textPrompts.length === 0) {
        showSnackbar('Please add at least one text prompt', 'warning');
        return;
      }
      
      setIsLoading(true);
      setError(null);
      
      const response = await yoloeApi.textPromptInference(currentImage.file, textPrompts);
      
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
      setError(error.message || 'Error during detection');
      showSnackbar(`Error: ${error.message || 'Failed to process detection'}`, 'error');
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
        Text Prompts
      </Typography>
      
      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
        Enter class names to detect. Each entry will be used as a separate class.
      </Typography>
      
      <Box sx={{ mb: 2, display: 'flex' }}>
        <TextField
          fullWidth
          size="small"
          variant="outlined"
          placeholder="Add class (e.g. 'car', 'person')"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={!currentImage}
          sx={{
            mr: 1,
            '& .MuiOutlinedInput-root': {
              '&.Mui-focused fieldset': {
                borderColor: 'primary.main',
              },
            },
          }}
        />
        <Button
          variant="contained"
          color="primary"
          onClick={handleAddPrompt}
          startIcon={<AddIcon />}
          disabled={!inputValue.trim() || !currentImage}
        >
          Add
        </Button>
      </Box>
      
      <Divider sx={{ mb: 2 }} />
      
      <Typography variant="subtitle2" color="textSecondary" gutterBottom>
        {textPrompts.length > 0 ? 'Classes to detect:' : 'No classes added yet'}
      </Typography>
      
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <Stack 
          direction="row" 
          spacing={1} 
          flexWrap="wrap"
          sx={{ my: 1, gap: 1 }}
        >
          {textPrompts.map((prompt, index) => (
            <Chip
              key={index}
              label={prompt}
              color="primary"
              variant="outlined"
              onDelete={() => removeTextPrompt(index)}
              deleteIcon={
                <IconButton size="small">
                  <DeleteIcon fontSize="small" />
                </IconButton>
              }
              sx={{
                borderRadius: 2,
                py: 0.5,
                bgcolor: 'rgba(238, 76, 44, 0.04)',
                borderColor: 'primary.main',
                '& .MuiChip-label': {
                  color: 'primary.dark',
                },
              }}
            />
          ))}
        </Stack>
      </Box>
      
      <Box sx={{ mt: 'auto' }}>
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          {textPrompts.length > 0 && (
            <Button
              variant="outlined"
              color="primary"
              onClick={clearTextPrompts}
              size="small"
            >
              Clear All
            </Button>
          )}
          
          <Button
            variant="contained"
            color="primary"
            startIcon={<SearchIcon />}
            onClick={handleDetection}
            disabled={isLoading || !currentImage || textPrompts.length === 0}
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

export default TextPromptPanel; 