/**
 * Photo Upload Handler
 * Handles static photo upload for room visualization
 */

export class PhotoUploadHandler {
  constructor() {
    this.uploadedPhotos = [];
    this.maxPhotos = 5;
  }

  /**
   * Create file input element for photo selection
   */
  createFileInput() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/jpeg,image/jpg,image/png';
    input.multiple = true;
    input.style.display = 'none';
    return input;
  }

  /**
   * Handle file selection from user
   */
  async handleFileSelection(files) {
    const validFiles = Array.from(files).filter(file => {
      const isValid = file.type.startsWith('image/');
      const isUnderLimit = this.uploadedPhotos.length < this.maxPhotos;
      return isValid && isUnderLimit;
    });

    const photoPromises = validFiles.map(file => this.readFileAsBase64(file));
    const photoDataArray = await Promise.all(photoPromises);

    photoDataArray.forEach(photoData => {
      if (this.uploadedPhotos.length < this.maxPhotos) {
        this.uploadedPhotos.push(photoData);
      }
    });

    return this.uploadedPhotos;
  }

  /**
   * Read file and convert to base64
   */
  readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        const base64String = e.target.result.split(',')[1]; // Remove data:image/jpeg;base64, prefix
        resolve({
          data: base64String,
          name: file.name,
          type: file.type,
          size: file.size,
          preview: e.target.result // Keep full data URL for preview
        });
      };

      reader.onerror = (error) => {
        console.error('Error reading file:', error);
        reject(error);
      };

      reader.readAsDataURL(file);
    });
  }

  /**
   * Remove photo by index
   */
  removePhoto(index) {
    if (index >= 0 && index < this.uploadedPhotos.length) {
      this.uploadedPhotos.splice(index, 1);
    }
    return this.uploadedPhotos;
  }

  /**
   * Clear all uploaded photos
   */
  clearPhotos() {
    this.uploadedPhotos = [];
  }

  /**
   * Get all uploaded photos
   */
  getPhotos() {
    return this.uploadedPhotos;
  }

  /**
   * Get base64 data only (without metadata)
   */
  getPhotoData() {
    return this.uploadedPhotos.map(photo => photo.data);
  }

  /**
   * Check if photos are uploaded
   */
  hasPhotos() {
    return this.uploadedPhotos.length > 0;
  }

  /**
   * Get count of uploaded photos
   */
  getPhotoCount() {
    return this.uploadedPhotos.length;
  }

  /**
   * Check if max photos reached
   */
  isMaxReached() {
    return this.uploadedPhotos.length >= this.maxPhotos;
  }
}
