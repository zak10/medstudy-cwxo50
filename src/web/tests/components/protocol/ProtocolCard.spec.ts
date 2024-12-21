import { describe, it, expect, vi } from 'vitest'; // v0.34.0
import { mount } from '@vue/test-utils'; // v2.4.0
import userEvent from '@testing-library/user-event'; // v14.0.0
import { axe } from '@axe-core/vue'; // v4.7.0

import ProtocolCard from '@/components/protocol/ProtocolCard.vue';
import ProtocolProgress from '@/components/protocol/ProtocolProgress.vue';
import type { Protocol, ProtocolStatus } from '@/types/protocol';

// Mock protocol data factory
const createMockProtocol = (overrides = {}): Protocol => ({
  id: 'test-protocol-1',
  title: 'Vitamin D Study',
  description: 'A comprehensive study of Vitamin D supplementation effects',
  duration: 12, // weeks
  status: ProtocolStatus.ACTIVE,
  participantCount: 32,
  imageUrl: 'https://example.com/protocol-image.jpg',
  requirements: [],
  safetyParams: [
    {
      id: 'age-range',
      metric: 'age',
      minValue: 18,
      maxValue: 65,
      unit: 'years'
    }
  ],
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-01-01T00:00:00Z',
  metadata: {},
  ...overrides
});

// Helper function to mount component with common options
const mountComponent = (props = {}, options = {}) => {
  return mount(ProtocolCard, {
    props: {
      protocol: createMockProtocol(),
      interactive: true,
      showProgress: false,
      loading: false,
      highContrast: false,
      ...props
    },
    global: {
      stubs: {
        BaseCard: true,
        BaseButton: true,
        ProtocolProgress: true
      },
      mocks: {
        $t: (key: string) => key // i18n mock
      },
      ...options
    }
  });
};

describe('ProtocolCard', () => {
  // Basic Rendering Tests
  describe('rendering', () => {
    it('renders protocol information correctly', () => {
      const wrapper = mountComponent();
      
      expect(wrapper.find('.protocol-card__title').text()).toBe('Vitamin D Study');
      expect(wrapper.find('.protocol-card__description').text()).toContain('comprehensive study');
      expect(wrapper.find('.protocol-card__status').exists()).toBe(true);
      expect(wrapper.find('.metric__value').text()).toBe('32');
    });

    it('renders protocol image when imageUrl is provided', () => {
      const wrapper = mountComponent();
      const img = wrapper.find('.protocol-card__image');
      
      expect(img.exists()).toBe(true);
      expect(img.attributes('src')).toBe('https://example.com/protocol-image.jpg');
      expect(img.attributes('alt')).toContain('Vitamin D Study');
    });

    it('handles missing optional properties gracefully', () => {
      const wrapper = mountComponent({
        protocol: createMockProtocol({ imageUrl: undefined })
      });
      
      expect(wrapper.find('.protocol-card__image').exists()).toBe(false);
    });
  });

  // Interaction Tests
  describe('interactions', () => {
    it('emits view event on card click when interactive', async () => {
      const wrapper = mountComponent();
      await wrapper.trigger('click');
      
      expect(wrapper.emitted('view')).toBeTruthy();
      expect(wrapper.emitted('view')?.[0]).toEqual(['test-protocol-1']);
    });

    it('emits enroll event on enroll button click', async () => {
      const wrapper = mountComponent();
      await wrapper.find('[data-test="enroll-button"]').trigger('click');
      
      expect(wrapper.emitted('enroll')).toBeTruthy();
      expect(wrapper.emitted('enroll')?.[0]).toEqual(['test-protocol-1']);
    });

    it('prevents interactions when loading', async () => {
      const wrapper = mountComponent({ loading: true });
      await wrapper.trigger('click');
      
      expect(wrapper.emitted('view')).toBeFalsy();
      expect(wrapper.find('[data-test="enroll-button"]').attributes('disabled')).toBe('true');
    });

    it('handles keyboard navigation correctly', async () => {
      const wrapper = mountComponent();
      await wrapper.trigger('keypress', { key: 'Enter' });
      
      expect(wrapper.emitted('view')).toBeTruthy();
    });
  });

  // Conditional Rendering Tests
  describe('conditional rendering', () => {
    it('shows progress component when showProgress is true', () => {
      const wrapper = mountComponent({ showProgress: true });
      expect(wrapper.findComponent(ProtocolProgress).exists()).toBe(true);
    });

    it('applies high contrast styles when enabled', () => {
      const wrapper = mountComponent({ highContrast: true });
      expect(wrapper.classes()).toContain('protocol-card--high-contrast');
    });

    it('applies correct status color based on protocol status', () => {
      const wrapper = mountComponent({
        protocol: createMockProtocol({ status: ProtocolStatus.PAUSED })
      });
      
      const statusIndicator = wrapper.find('.protocol-card__status');
      expect(statusIndicator.attributes('style')).toContain('background-color: #F1C40F');
    });
  });

  // Accessibility Tests
  describe('accessibility', () => {
    it('meets WCAG 2.1 AA standards', async () => {
      const wrapper = mountComponent();
      const results = await axe(wrapper.element);
      expect(results.violations).toHaveLength(0);
    });

    it('provides proper ARIA labels and roles', () => {
      const wrapper = mountComponent();
      
      expect(wrapper.attributes('role')).toBe('article');
      expect(wrapper.attributes('aria-label')).toBe('Vitamin D Study');
      expect(wrapper.find('.protocol-card__status').attributes('role')).toBe('status');
    });

    it('maintains keyboard focus indicators', async () => {
      const wrapper = mountComponent();
      await wrapper.trigger('focus');
      
      expect(wrapper.classes()).toContain('protocol-card--focused');
    });
  });

  // Responsive Behavior Tests
  describe('responsive behavior', () => {
    it('adapts layout for mobile viewport', () => {
      const wrapper = mountComponent({}, {
        data() {
          return {
            windowWidth: 320
          };
        }
      });
      
      expect(wrapper.classes()).toContain('protocol-card--mobile');
    });

    it('adjusts image size for different viewports', () => {
      const wrapper = mountComponent({}, {
        data() {
          return {
            windowWidth: 768
          };
        }
      });
      
      const image = wrapper.find('.protocol-card__image');
      expect(image.classes()).toContain('protocol-card__image--tablet');
    });
  });

  // Error Handling Tests
  describe('error handling', () => {
    it('emits error event on interaction failure', async () => {
      const error = new Error('Interaction failed');
      const wrapper = mountComponent({}, {
        methods: {
          handleClick: () => { throw error; }
        }
      });
      
      await wrapper.trigger('click');
      expect(wrapper.emitted('error')?.[0]).toEqual([error]);
    });

    it('displays fallback content when image fails to load', async () => {
      const wrapper = mountComponent();
      const img = wrapper.find('.protocol-card__image');
      await img.trigger('error');
      
      expect(wrapper.find('.protocol-card__image-fallback').exists()).toBe(true);
    });
  });
});