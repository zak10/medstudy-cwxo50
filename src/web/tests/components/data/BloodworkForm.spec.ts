// External imports - v3.3.0
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount, VueWrapper } from '@vue/test-utils';
import { flushPromises } from '@vue/test-utils';

// Internal imports
import BloodworkForm from '@/components/data/BloodworkForm.vue';
import { BloodWorkData } from '@/types/data';
import { MARKER_RANGES, APPROVED_LABS } from '@/utils/validation';
import { useDataCollection } from '@/composables/useDataCollection';
import { theme } from '@/config/theme';

// Mock the composables
vi.mock('@/composables/useDataCollection', () => ({
  useDataCollection: vi.fn(() => ({
    submitBloodWork: vi.fn(),
    validationErrors: [],
    isSubmitting: false,
    uploadProgress: 0,
    handleFileSelect: vi.fn()
  }))
}));

// Test data
const validBloodWorkData: BloodWorkData = {
  markers: {
    vitamin_d: 45,
    b12: 500
  },
  testDate: new Date('2023-09-01'),
  labName: 'LabCorp',
  fileHash: 'abc123',
  reportFileUrl: '',
  encryptionMetadata: {
    algorithm: 'AES-256-GCM',
    keyId: 'test-key',
    encryptedAt: new Date(),
    version: '1.0'
  }
};

const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

describe('BloodworkForm', () => {
  let wrapper: VueWrapper;
  let mockSubmitBloodWork: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Reset mocks
    mockSubmitBloodWork = vi.fn();
    (useDataCollection as any).mockImplementation(() => ({
      submitBloodWork: mockSubmitBloodWork,
      validationErrors: [],
      isSubmitting: false,
      uploadProgress: 0,
      handleFileSelect: vi.fn()
    }));

    // Mount component
    wrapper = mount(BloodworkForm, {
      props: {
        protocolId: 'test-protocol'
      },
      global: {
        provide: {
          theme
        }
      }
    });
  });

  afterEach(() => {
    wrapper.unmount();
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('renders all form sections correctly', () => {
      // Test date section
      expect(wrapper.find('input[type="date"]').exists()).toBe(true);
      
      // Lab information section
      expect(wrapper.find('input[list="approved-labs"]').exists()).toBe(true);
      expect(wrapper.find('#approved-labs').exists()).toBe(true);
      
      // Blood markers section
      const markerInputs = wrapper.findAll('.marker-field');
      expect(markerInputs.length).toBe(Object.keys(MARKER_RANGES).length);
      
      // File upload section
      expect(wrapper.find('.upload-zone').exists()).toBe(true);
      expect(wrapper.find('input[type="file"]').exists()).toBe(true);
    });

    it('displays approved labs in datalist', () => {
      const options = wrapper.findAll('#approved-labs option');
      expect(options.length).toBe(APPROVED_LABS.length);
      APPROVED_LABS.forEach((lab, index) => {
        expect(options[index].attributes('value')).toBe(lab);
      });
    });
  });

  describe('Form Validation', () => {
    it('validates required fields', async () => {
      const submitButton = wrapper.find('button[type="submit"]');
      await submitButton.trigger('click');
      
      await flushPromises();
      
      // Check that validation errors are displayed
      const errors = wrapper.findAll('.validation-errors .error-item');
      expect(errors.length).toBeGreaterThan(0);
      expect(mockSubmitBloodWork).not.toHaveBeenCalled();
    });

    it('validates marker ranges', async () => {
      // Set invalid marker value
      await wrapper.find('input[name="vitamin_d"]').setValue(-1);
      
      const submitButton = wrapper.find('button[type="submit"]');
      await submitButton.trigger('click');
      
      await flushPromises();
      
      // Check for range validation error
      const errors = wrapper.findAll('.validation-errors .error-item');
      expect(errors.some(e => e.text().includes('outside valid range'))).toBe(true);
    });

    it('validates lab name against approved list', async () => {
      await wrapper.find('input[list="approved-labs"]').setValue('Invalid Lab');
      
      const submitButton = wrapper.find('button[type="submit"]');
      await submitButton.trigger('click');
      
      await flushPromises();
      
      // Check for invalid lab error
      const errors = wrapper.findAll('.validation-errors .error-item');
      expect(errors.some(e => e.text().includes('Laboratory not in approved list'))).toBe(true);
    });
  });

  describe('File Handling', () => {
    it('handles file upload correctly', async () => {
      const fileInput = wrapper.find('input[type="file"]');
      await fileInput.trigger('change', { target: { files: [mockFile] } });
      
      await flushPromises();
      
      // Check file preview is displayed
      expect(wrapper.find('.file-preview').exists()).toBe(true);
      expect(wrapper.find('.file-preview').text()).toContain('test.pdf');
    });

    it('validates file type restrictions', async () => {
      const invalidFile = new File(['test'], 'test.exe', { type: 'application/x-msdownload' });
      const fileInput = wrapper.find('input[type="file"]');
      
      await fileInput.trigger('change', { target: { files: [invalidFile] } });
      await flushPromises();
      
      // Check for file type error
      const errors = wrapper.findAll('.validation-errors .error-item');
      expect(errors.some(e => e.text().includes('file type'))).toBe(true);
    });
  });

  describe('Form Submission', () => {
    it('submits valid form data successfully', async () => {
      // Fill form with valid data
      await wrapper.find('input[type="date"]').setValue('2023-09-01');
      await wrapper.find('input[list="approved-labs"]').setValue('LabCorp');
      await wrapper.find('input[name="vitamin_d"]').setValue(45);
      await wrapper.find('input[name="b12"]').setValue(500);
      
      const fileInput = wrapper.find('input[type="file"]');
      await fileInput.trigger('change', { target: { files: [mockFile] } });
      
      await flushPromises();
      
      // Submit form
      const submitButton = wrapper.find('button[type="submit"]');
      await submitButton.trigger('click');
      
      await flushPromises();
      
      // Verify submission
      expect(mockSubmitBloodWork).toHaveBeenCalledWith(expect.objectContaining({
        markers: {
          vitamin_d: 45,
          b12: 500
        },
        labName: 'LabCorp',
        testDate: expect.any(Date)
      }));
    });

    it('handles submission errors gracefully', async () => {
      mockSubmitBloodWork.mockRejectedValue(new Error('Submission failed'));
      
      // Fill form with valid data
      await wrapper.find('input[type="date"]').setValue('2023-09-01');
      await wrapper.find('input[list="approved-labs"]').setValue('LabCorp');
      await wrapper.find('input[name="vitamin_d"]').setValue(45);
      
      const submitButton = wrapper.find('button[type="submit"]');
      await submitButton.trigger('click');
      
      await flushPromises();
      
      // Check error handling
      const errors = wrapper.findAll('.validation-errors .error-item');
      expect(errors.some(e => e.text().includes('Submission failed'))).toBe(true);
    });
  });

  describe('Security Features', () => {
    it('applies field-level encryption for sensitive data', async () => {
      // Fill sensitive fields
      await wrapper.find('input[list="approved-labs"]').setValue('LabCorp');
      await wrapper.find('input[name="vitamin_d"]').setValue(45);
      
      const submitButton = wrapper.find('button[type="submit"]');
      await submitButton.trigger('click');
      
      await flushPromises();
      
      // Verify encryption metadata is included
      expect(mockSubmitBloodWork).toHaveBeenCalledWith(
        expect.objectContaining({
          encryptionMetadata: expect.objectContaining({
            algorithm: 'AES-256-GCM',
            version: '1.0'
          })
        })
      );
    });

    it('sanitizes user input', async () => {
      const maliciousInput = '<script>alert("xss")</script>LabCorp';
      await wrapper.find('input[list="approved-labs"]').setValue(maliciousInput);
      
      const submitButton = wrapper.find('button[type="submit"]');
      await submitButton.trigger('click');
      
      await flushPromises();
      
      // Verify sanitized input
      expect(mockSubmitBloodWork).toHaveBeenCalledWith(
        expect.objectContaining({
          labName: expect.not.stringContaining('<script>')
        })
      );
    });
  });
});