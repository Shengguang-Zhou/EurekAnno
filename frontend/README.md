# EurekAnno - YOLOe Frontend

A React-based frontend for YOLOe object detection.

## Features

- Image upload and gallery management
- Three detection modes:
  - Text-prompt: Detect objects using text descriptions
  - Image-prompt: Draw bounding boxes to guide detection
  - Prompt-free: Automatic detection without prompts
- Interactive annotation canvas
- Real-time detection visualization
- Export to YOLO format
- Responsive design

## Technologies Used

- React 18
- Material UI 5
- React Konva for canvas operations
- Axios for API communication

## Getting Started

### Prerequisites

- Node.js 16+ and npm

### Installation

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Start the development server:

```bash
npm start
```

This will run the app in development mode at [http://localhost:3000](http://localhost:3000)

## Usage

1. Upload an image using the upload area or drag-and-drop.
2. Select a detection mode from the sidebar:
   - **Text Prompt**: Enter class names to detect specific objects
   - **Image Prompt**: Draw bounding boxes on the image to guide detection
   - **Prompt Free**: Use automatic detection without any prompts
3. Click "Detect Objects" to start detection
4. View results on the canvas and in the results panel
5. Export detected objects to YOLO format

## Project Structure

- `/src/components` - React components
- `/src/context` - Application state management
- `/src/api` - API service for YOLOe
- `/src/utils` - Utility functions and theme

## License

This project is licensed under the MIT License. 