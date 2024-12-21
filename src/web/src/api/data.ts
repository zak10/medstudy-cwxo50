// @version axios ^1.4.0
// @version clamav.js ^1.0.0
import axios, { AxiosProgressEvent } from 'axios';
import ClamAV from 'clamav.js';

// Internal imports
import { APIResponse } from './types';
import { DataPoint } from '../types/data';
import { ENDPOINTS } from '../config/api';

// Constants for file handling
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_FILE_TYPES = ['.pdf', '.jpg', '.png'];
const MIME_TYPE_MAP = {
  '.pdf': 'application/pdf',
  '.jpg': 'image/jpeg',
  '.png': 'image/png'
};
const CHUNK_SIZE = 1024 * 1024; // 1MB chunks for upload
const MAX_RETRIES = 3;

// Types for file upload
interface ProgressCallback {
  (progress: number): void;
}

interface UploadOptions {
  onProgress?: ProgressCallback;
  signal?: AbortSignal;
}

interface FileValidationResult {
  valid: boolean;
  errors: string[];
}

/**
 * Validates file before upload
 * @param file File to validate
 * @returns Validation result with any errors
 */
async function validateFile(file: File): Promise<FileValidationResult> {
  const errors: string[] = [];

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    errors.push(`File size exceeds maximum allowed size of ${MAX_FILE_SIZE / 1024 / 1024}MB`);
  }

  // Check file type
  const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;
  if (!ALLOWED_FILE_TYPES.includes(fileExtension)) {
    errors.push(`File type ${fileExtension} not allowed. Supported types: ${ALLOWED_FILE_TYPES.join(', ')}`);
  }

  // Verify MIME type
  const actualMimeType = file.type;
  const expectedMimeType = MIME_TYPE_MAP[fileExtension as keyof typeof MIME_TYPE_MAP];
  if (actualMimeType !== expectedMimeType) {
    errors.push('File MIME type does not match extension');
  }

  // Virus scan
  try {
    const clam = new ClamAV();
    const scanResult = await clam.scanBuffer(await file.arrayBuffer());
    if (scanResult.isInfected) {
      errors.push('File failed virus scan');
    }
  } catch (error) {
    errors.push('Virus scan failed');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Calculates file hash for integrity verification
 * @param file File to hash
 * @returns SHA-256 hash of file
 */
async function calculateFileHash(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Submits a new data point with validation
 * @param dataPoint Data point to submit
 * @param signal Optional AbortSignal for request cancellation
 * @returns API response with submitted data point
 */
export async function submitDataPoint(
  dataPoint: DataPoint,
  signal?: AbortSignal
): Promise<APIResponse<DataPoint>> {
  let retries = 0;

  while (retries < MAX_RETRIES) {
    try {
      const response = await axios.post<APIResponse<DataPoint>>(
        ENDPOINTS.DATA.SUBMIT,
        dataPoint,
        {
          signal,
          headers: {
            'Content-Type': 'application/json',
            'X-Request-ID': crypto.randomUUID()
          }
        }
      );

      return response.data;
    } catch (error) {
      if (axios.isCancel(error)) {
        throw error;
      }

      retries++;
      if (retries === MAX_RETRIES) {
        throw error;
      }

      // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, retries) * 1000));
    }
  }

  throw new Error('Maximum retries exceeded');
}

/**
 * Uploads blood work file with progress tracking and validation
 * @param file File to upload
 * @param data Associated blood work data
 * @param options Upload options including progress callback
 * @returns API response with uploaded data point
 */
export async function uploadBloodWork(
  file: File,
  data: Record<string, any>,
  options?: UploadOptions
): Promise<APIResponse<DataPoint>> {
  // Validate file
  const validationResult = await validateFile(file);
  if (!validationResult.valid) {
    throw new Error(`File validation failed: ${validationResult.errors.join(', ')}`);
  }

  // Calculate file hash
  const fileHash = await calculateFileHash(file);

  // Prepare form data
  const formData = new FormData();
  formData.append('file', file);
  formData.append('data', JSON.stringify({
    ...data,
    fileHash
  }));

  try {
    const response = await axios.post<APIResponse<DataPoint>>(
      ENDPOINTS.DATA.UPLOAD,
      formData,
      {
        signal: options?.signal,
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-Request-ID': crypto.randomUUID()
        },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (progressEvent.total && options?.onProgress) {
            const progress = (progressEvent.loaded / progressEvent.total) * 100;
            options.onProgress(progress);
          }
        }
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isCancel(error)) {
      throw error;
    }
    throw error;
  }
}