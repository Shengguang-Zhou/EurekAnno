import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1/yoloe';

// Helper to create form data
const createFormData = (image, params = {}) => {
  const formData = new FormData();
  formData.append('file', image);
  
  Object.entries(params).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach(val => formData.append(key, val));
    } else if (value !== null && value !== undefined) {
      formData.append(key, value);
    }
  });
  
  return formData;
};

export const yoloeApi = {
  // Prompt-free inference
  promptFreeInference: async (image, params = {}) => {
    const formData = createFormData(image, params);
    const response = await axios.post(`${API_URL}/prompt-free`, formData);
    return response.data;
  },
  
  // Text-prompt inference
  textPromptInference: async (image, classNames, params = {}) => {
    const formData = createFormData(image, { 
      ...params, 
      class_names: classNames 
    });
    const response = await axios.post(`${API_URL}/text-prompt`, formData);
    return response.data;
  },
  
  // Image-prompt inference
  imagePromptInference: async (image, bboxes, cls, params = {}) => {
    const formData = createFormData(image, {
      ...params,
      bboxes: JSON.stringify(bboxes),
      cls: JSON.stringify(cls)
    });
    
    if (params.referImage) {
      formData.append('refer_file', params.referImage);
    }
    
    const response = await axios.post(`${API_URL}/image-prompt`, formData);
    return response.data;
  },
  
  // Export single image annotations to YOLO format
  exportYolo: async (data) => {
    const response = await axios.post(`${API_URL}/export/yolo`, data, {
      responseType: 'blob'
    });
    return response.data;
  },
  
  // Export batch annotations to YOLO format
  exportYoloBatch: async (data) => {
    const response = await axios.post(`${API_URL}/export/yolo-batch`, data, {
      responseType: 'blob'
    });
    return response.data;
  }
};

export default yoloeApi; 