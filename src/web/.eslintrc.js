/** 
 * ESLint configuration for Medical Research Platform frontend
 * Enforces strict TypeScript type checking, Vue.js best practices, and code quality standards
 * @version 1.0.0
 */

module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true,
    jest: true
  },
  extends: [
    // Vue 3 recommended rules
    'plugin:vue/vue3-recommended',
    // TypeScript base rules
    'plugin:@typescript-eslint/recommended',
    // TypeScript strict type checking rules
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    // Prettier compatibility
    'prettier'
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'module',
    parser: '@typescript-eslint/parser',
    extraFileExtensions: ['.vue'],
    project: ['./tsconfig.json']
  },
  plugins: [
    '@typescript-eslint',
    'vue'
  ],
  rules: {
    // Vue.js specific rules
    'vue/script-setup-uses-vars': 'error',
    'vue/multi-word-component-names': 'error',
    'vue/component-definition-name-casing': ['error', 'PascalCase'],
    'vue/component-api-style': ['error', ['script-setup', 'composition']],

    // TypeScript strict type checking
    '@typescript-eslint/explicit-function-return-type': 'error',
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': ['error', {
      'argsIgnorePattern': '^_'
    }],
    '@typescript-eslint/strict-boolean-expressions': 'error',
    '@typescript-eslint/no-floating-promises': 'error',
    '@typescript-eslint/no-unsafe-assignment': 'error',
    '@typescript-eslint/restrict-template-expressions': 'error',

    // Code quality and complexity
    'complexity': ['error', 10], // Maximum cyclomatic complexity
    'no-console': ['warn', {
      'allow': ['warn', 'error']
    }],
    'no-debugger': 'warn',

    // Documentation requirements
    'require-jsdoc': ['error', {
      'require': {
        'FunctionDeclaration': true,
        'MethodDefinition': true,
        'ClassDeclaration': true
      }
    }]
  },
  overrides: [
    {
      // Special handling for Vue files
      files: ['*.vue'],
      parser: 'vue-eslint-parser',
      parserOptions: {
        parser: '@typescript-eslint/parser'
      }
    },
    {
      // Test file configuration
      files: ['*.spec.ts', '*.test.ts'],
      env: {
        jest: true
      },
      rules: {
        'require-jsdoc': 'off' // Disable JSDoc requirement for test files
      }
    }
  ]
};