import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, VueWrapper } from '@vue/test-utils';
import BaseButton from '@/components/common/BaseButton.vue';
import type { Theme } from '@/types/ui';

// Mock window.__theme__ for style testing
const mockTheme: Partial<Theme> = {
  colors: {
    primary: '#2C3E50',
    secondary: '#3498DB',
    accent: '#E74C3C'
  },
  elevation: {
    level1: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
  }
};

// Helper function to create wrapper with default or custom props
const createWrapper = (props = {}, slots = {}) => {
  return mount(BaseButton, {
    props,
    slots,
    global: {
      beforeMount() {
        Object.defineProperty(window, '__theme__', {
          value: mockTheme,
          writable: true
        });
      }
    }
  });
};

describe('BaseButton Component', () => {
  let wrapper: VueWrapper<any>;

  beforeEach(() => {
    wrapper = createWrapper();
  });

  afterEach(() => {
    wrapper.unmount();
  });

  describe('Rendering', () => {
    it('renders button element with default props', () => {
      expect(wrapper.element.tagName).toBe('BUTTON');
      expect(wrapper.classes()).toContain('base-button');
      expect(wrapper.classes()).toContain('variant-primary');
      expect(wrapper.classes()).toContain('size-md');
    });

    it('applies correct type attribute', () => {
      expect(wrapper.attributes('type')).toBe('button');
      
      wrapper = createWrapper({ type: 'submit' });
      expect(wrapper.attributes('type')).toBe('submit');
    });

    it('renders slot content correctly', () => {
      wrapper = createWrapper({}, {
        default: 'Button Text',
        prefix: '<span>Prefix</span>',
        suffix: '<span>Suffix</span>'
      });

      expect(wrapper.text()).toContain('Button Text');
      expect(wrapper.html()).toContain('<span>Prefix</span>');
      expect(wrapper.html()).toContain('<span>Suffix</span>');
    });
  });

  describe('Variants', () => {
    it.each(['primary', 'secondary', 'accent', 'outline', 'text'])(
      'applies correct classes and styles for %s variant',
      (variant) => {
        wrapper = createWrapper({ variant });
        expect(wrapper.classes()).toContain(`variant-${variant}`);
        
        if (['primary', 'secondary', 'accent'].includes(variant)) {
          expect(wrapper.attributes('style')).toContain('background-color');
        }
      }
    );
  });

  describe('Sizes', () => {
    it.each(['sm', 'md', 'lg'])('applies correct size class for %s size', (size) => {
      wrapper = createWrapper({ size });
      expect(wrapper.classes()).toContain(`size-${size}`);
    });
  });

  describe('States', () => {
    it('handles disabled state correctly', () => {
      wrapper = createWrapper({ disabled: true });
      expect(wrapper.classes()).toContain('disabled');
      expect(wrapper.attributes('disabled')).toBeDefined();
      expect(wrapper.attributes('aria-disabled')).toBe('true');
    });

    it('handles loading state correctly', () => {
      wrapper = createWrapper({ loading: true });
      expect(wrapper.classes()).toContain('loading');
      expect(wrapper.attributes('aria-busy')).toBe('true');
      expect(wrapper.findComponent({ name: 'LoadingSpinner' }).exists()).toBe(true);
      expect(wrapper.find('.button-content').exists()).toBe(false);
    });

    it('hides prefix and suffix slots during loading', () => {
      wrapper = createWrapper(
        { loading: true },
        {
          prefix: '<span>Prefix</span>',
          suffix: '<span>Suffix</span>'
        }
      );
      expect(wrapper.html()).not.toContain('<span>Prefix</span>');
      expect(wrapper.html()).not.toContain('<span>Suffix</span>');
    });
  });

  describe('Events', () => {
    it('emits click event when not disabled or loading', async () => {
      await wrapper.trigger('click');
      expect(wrapper.emitted('click')).toBeTruthy();
      expect(wrapper.emitted('click')![0][0]).toBeInstanceOf(MouseEvent);
    });

    it('does not emit click event when disabled', async () => {
      wrapper = createWrapper({ disabled: true });
      await wrapper.trigger('click');
      expect(wrapper.emitted('click')).toBeFalsy();
    });

    it('does not emit click event when loading', async () => {
      wrapper = createWrapper({ loading: true });
      await wrapper.trigger('click');
      expect(wrapper.emitted('click')).toBeFalsy();
    });
  });

  describe('Accessibility', () => {
    it('has correct ARIA attributes', () => {
      expect(wrapper.attributes('role')).toBe('button');
      
      wrapper = createWrapper({ ariaLabel: 'Test Button' });
      expect(wrapper.attributes('aria-label')).toBe('Test Button');
    });

    it('maintains focus visibility', async () => {
      await wrapper.trigger('focus');
      expect(getComputedStyle(wrapper.element).outline).not.toBe('none');
    });

    it('supports keyboard interaction', async () => {
      await wrapper.trigger('keydown.enter');
      expect(wrapper.emitted('click')).toBeTruthy();
      
      await wrapper.trigger('keydown.space');
      expect(wrapper.emitted('click')).toBeTruthy();
    });
  });

  describe('Style Integration', () => {
    it('applies theme colors correctly', () => {
      wrapper = createWrapper({ variant: 'primary' });
      expect(wrapper.attributes('style')).toContain(`background-color: ${mockTheme.colors.primary}`);
    });

    it('applies elevation styles when not disabled', () => {
      expect(wrapper.attributes('style')).toContain(mockTheme.elevation.level1);
      
      wrapper = createWrapper({ disabled: true });
      expect(wrapper.attributes('style')).not.toContain(mockTheme.elevation.level1);
    });

    it('handles RTL support', () => {
      // Simulate RTL direction
      document.dir = 'rtl';
      wrapper = createWrapper({}, {
        prefix: '<span>Prefix</span>',
        suffix: '<span>Suffix</span>'
      });
      
      expect(wrapper.classes()).toContain('with-prefix');
      expect(wrapper.classes()).toContain('with-suffix');
      
      // Reset direction
      document.dir = 'ltr';
    });
  });
});