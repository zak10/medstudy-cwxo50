<template>
  <form 
    class="register-form"
    @submit="handleSubmit"
    novalidate
  >
    <div class="register-form__fields">
      <!-- Email Field -->
      <BaseInput
        v-model="formData.email"
        type="email"
        label="Email Address"
        :error="errors.email"
        required
        :validation-rules="validationRules.email"
        aria-label="Email Address"
      />

      <!-- Password Field -->
      <BaseInput
        v-model="formData.password"
        type="password"
        label="Password"
        :error="errors.password"
        required
        :validation-rules="validationRules.password"
        aria-label="Password"
      />

      <!-- Password Confirmation Field -->
      <BaseInput
        v-model="formData.confirmPassword"
        type="password"
        label="Confirm Password"
        :error="errors.confirmPassword"
        required
        :validation-rules="validationRules.confirmPassword"
        aria-label="Confirm Password"
      />

      <!-- First Name Field -->
      <BaseInput
        v-model="formData.firstName"
        type="text"
        label="First Name"
        :error="errors.firstName"
        required
        :validation-rules="validationRules.firstName"
        aria-label="First Name"
      />

      <!-- Last Name Field -->
      <BaseInput
        v-model="formData.lastName"
        type="text"
        label="Last Name"
        :error="errors.lastName"
        required
        :validation-rules="validationRules.lastName"
        aria-label="Last Name"
      />

      <!-- Role Selection -->
      <div class="register-form__role-select">
        <label id="role-label">Select Role</label>
        <select
          v-model="formData.role"
          :aria-labelledby="'role-label'"
          :aria-invalid="!!errors.role"
          required
        >
          <option value="PARTICIPANT">Study Participant</option>
          <option value="PROTOCOL_CREATOR">Protocol Creator</option>
          <option value="PARTNER">Supplement Partner</option>
        </select>
        <span v-if="errors.role" class="error-message" role="alert">
          {{ errors.role }}
        </span>
      </div>
    </div>

    <!-- Password Strength Indicator -->
    <div 
      v-if="formData.password"
      class="password-strength"
      :aria-label="`Password strength: ${passwordStrengthLabel}`"
    >
      <div 
        class="password-strength__bar"
        :style="{ width: `${passwordStrength}%` }"
        :class="passwordStrengthClass"
      ></div>
    </div>

    <!-- Submit Button -->
    <BaseButton
      type="submit"
      variant="primary"
      :loading="loading"
      :disabled="!isFormValid"
      aria-label="Create Account"
    >
      Create Account
    </BaseButton>
  </form>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue';
import { useAuth } from '@/composables/useAuth';
import BaseInput from '@/components/common/BaseInput.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import { RegisterCredentials, UserRole } from '@/types/auth';
import zxcvbn from 'zxcvbn'; // v4.4.2

export default defineComponent({
  name: 'RegisterForm',

  components: {
    BaseInput,
    BaseButton
  },

  emits: ['registration-success'],

  setup(_, { emit }) {
    const { handleRegister } = useAuth();

    // Form data with type safety
    const formData = ref<RegisterCredentials>({
      email: '',
      password: '',
      confirmPassword: '',
      firstName: '',
      lastName: '',
      role: UserRole.PARTICIPANT
    });

    // Form state
    const loading = ref(false);
    const errors = ref<Record<string, string>>({});

    // Validation rules
    const validationRules = {
      email: [
        {
          validate: (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
          message: 'Please enter a valid email address'
        }
      ],
      password: [
        {
          validate: (value: string) => value.length >= 12,
          message: 'Password must be at least 12 characters'
        },
        {
          validate: (value: string) => /[A-Z]/.test(value),
          message: 'Password must contain at least one uppercase letter'
        },
        {
          validate: (value: string) => /[a-z]/.test(value),
          message: 'Password must contain at least one lowercase letter'
        },
        {
          validate: (value: string) => /\d/.test(value),
          message: 'Password must contain at least one number'
        },
        {
          validate: (value: string) => /[!@#$%^&*]/.test(value),
          message: 'Password must contain at least one special character'
        }
      ],
      confirmPassword: [
        {
          validate: (value: string) => value === formData.value.password,
          message: 'Passwords must match'
        }
      ],
      firstName: [
        {
          validate: (value: string) => value.length >= 2,
          message: 'First name must be at least 2 characters'
        }
      ],
      lastName: [
        {
          validate: (value: string) => value.length >= 2,
          message: 'Last name must be at least 2 characters'
        }
      ]
    };

    // Password strength computation
    const passwordStrength = computed(() => {
      if (!formData.value.password) return 0;
      const result = zxcvbn(formData.value.password);
      return (result.score / 4) * 100;
    });

    const passwordStrengthClass = computed(() => {
      const strength = passwordStrength.value;
      if (strength >= 75) return 'strong';
      if (strength >= 50) return 'medium';
      return 'weak';
    });

    const passwordStrengthLabel = computed(() => {
      const strength = passwordStrength.value;
      if (strength >= 75) return 'Strong';
      if (strength >= 50) return 'Medium';
      return 'Weak';
    });

    // Form validation
    const isFormValid = computed(() => {
      return Object.keys(errors.value).length === 0 &&
        formData.value.email &&
        formData.value.password &&
        formData.value.confirmPassword &&
        formData.value.firstName &&
        formData.value.lastName &&
        formData.value.role;
    });

    // Form submission handler
    const handleSubmit = async (event: Event) => {
      event.preventDefault();
      
      if (!isFormValid.value) return;

      try {
        loading.value = true;
        errors.value = {};

        const success = await handleRegister(formData.value);
        
        if (success) {
          emit('registration-success', formData.value);
        }
      } catch (error) {
        errors.value = {
          form: error instanceof Error ? error.message : 'Registration failed'
        };
      } finally {
        loading.value = false;
      }
    };

    return {
      formData,
      loading,
      errors,
      validationRules,
      passwordStrength,
      passwordStrengthClass,
      passwordStrengthLabel,
      isFormValid,
      handleSubmit
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;

.register-form {
  display: flex;
  flex-direction: column;
  gap: vars.spacing(4);
  max-width: 480px;
  margin: 0 auto;
  padding: vars.spacing(4);

  &__fields {
    display: flex;
    flex-direction: column;
    gap: vars.spacing(3);
  }

  &__role-select {
    display: flex;
    flex-direction: column;
    gap: vars.spacing(1);

    select {
      height: 40px;
      padding: 0 vars.spacing(2);
      border: 1px solid color(gray, 300);
      border-radius: 4px;
      background-color: white;
      font-family: vars.$font-family-primary;
      font-size: 1rem;

      &:focus {
        outline: none;
        border-color: color(primary);
        box-shadow: 0 0 0 2px rgba(color(primary), 0.2);
      }

      &[aria-invalid="true"] {
        border-color: color(error);
      }
    }
  }

  .password-strength {
    height: 4px;
    background-color: color(gray, 200);
    border-radius: 2px;
    overflow: hidden;

    &__bar {
      height: 100%;
      transition: width 0.3s ease-out;

      &.weak {
        background-color: color(error);
      }

      &.medium {
        background-color: color(warning);
      }

      &.strong {
        background-color: color(success);
      }
    }
  }

  .error-message {
    color: color(error);
    font-size: 0.875rem;
    margin-top: vars.spacing(1);
  }
}
</style>