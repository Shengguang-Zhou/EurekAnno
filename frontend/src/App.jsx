import React from 'react';
import { 
  Box, 
  CssBaseline, 
  Grid, 
  ThemeProvider, 
  Typography,
  AppBar,
  Toolbar,
  useMediaQuery
} from '@mui/material';
import { AppProvider, useApp, DETECTION_MODES } from './context/AppContext';
import theme from './utils/theme';

// Components
import Sidebar from './components/Sidebar';
import ImageUploader from './components/ImageUploader';
import AnnotationCanvas from './components/AnnotationCanvas';
import TextPromptPanel from './components/TextPromptPanel';
import ImagePromptPanel from './components/ImagePromptPanel';
import PromptFreePanel from './components/PromptFreePanel';
import DetectionControls from './components/DetectionControls';
import ResultsPanel from './components/ResultsPanel';
import ImageGallery from './components/ImageGallery';

const AppContent = () => {
  const { detectionMode, currentImage } = useApp();
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));
  
  // Render the appropriate panel based on current detection mode
  const renderModePanel = () => {
    switch (detectionMode) {
      case DETECTION_MODES.TEXT_PROMPT:
        return <TextPromptPanel />;
      case DETECTION_MODES.IMAGE_PROMPT:
        return <ImagePromptPanel />;
      case DETECTION_MODES.PROMPT_FREE:
        return <PromptFreePanel />;
      default:
        return <TextPromptPanel />;
    }
  };
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* App Bar */}
      <AppBar position="static" color="default" elevation={0} sx={{ borderBottom: '1px solid', borderColor: 'divider' }}>
        <Toolbar>
          <Typography
            variant="h6"
            color="primary"
            component="div"
            sx={{ 
              flexGrow: 1, 
              fontWeight: 700,
              letterSpacing: '-0.5px',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            EurekAnno
            <Typography
              variant="caption"
              sx={{
                ml: 1,
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
                px: 1,
                py: 0.5,
                borderRadius: 1,
                fontWeight: 600
              }}
            >
              YOLOe
            </Typography>
          </Typography>
        </Toolbar>
      </AppBar>
      
      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          overflow: 'hidden',
          p: 3,
          bgcolor: 'background.default'
        }}
      >
        <Grid container spacing={3} sx={{ height: '100%' }}>
          {/* Left Sidebar */}
          <Grid item xs={12} md={3} lg={2} sx={{ height: isMobile ? 'auto' : '100%' }}>
            <Grid container spacing={3} sx={{ height: '100%' }}>
              {/* Mode Selection */}
              <Grid item xs={12} sx={{ height: '50%' }}>
                <Sidebar />
              </Grid>
              
              {/* Mode Panel (with inputs and detect button) */}
              <Grid item xs={12} sx={{ height: '50%' }}>
                {renderModePanel()}
              </Grid>
            </Grid>
          </Grid>
          
          {/* Main Canvas Area - Center, larger */}
          <Grid item xs={12} md={6} lg={7} sx={{ height: '100%' }}>
            {currentImage ? (
              <AnnotationCanvas />
            ) : (
              <ImageUploader />
            )}
          </Grid>
          
          {/* Right Sidebar */}
          <Grid item xs={12} md={3} lg={3} sx={{ height: isMobile ? 'auto' : '100%' }}>
            <Grid container spacing={3} sx={{ height: '100%' }}>
              {/* Image Gallery - Upper right */}
              <Grid item xs={12} sx={{ height: '60%' }}>
                <ImageGallery />
              </Grid>
              
              {/* Detection Controls - Middle right */}
              <Grid item xs={12} sx={{ height: '15%' }}>
                <DetectionControls />
              </Grid>
              
              {/* Results Panel - Bottom right */}
              <Grid item xs={12} sx={{ height: '25%' }}>
                <ResultsPanel />
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

const App = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppProvider>
        <AppContent />
      </AppProvider>
    </ThemeProvider>
  );
};

export default App; 