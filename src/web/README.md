# Medical Research Platform Frontend

A Vue.js-based frontend application for the Medical Research Platform, enabling community-driven medical research through structured protocols and data collection.

## Prerequisites

- Node.js >= 18.16.0
- npm >= 9.0.0
- Git

## Technology Stack

- Vue.js v3.3.0
- TypeScript 5.0.0
- Vite 4.4.0
- Vuetify 3.3.0
- Pinia 2.1.0
- Vue Router 4.2.0

## Getting Started

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd src/web
```

2. Install dependencies:
```bash
npm install
```

3. Create environment files:
```bash
cp .env.example .env.development
cp .env.example .env.production
```

4. Start development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

## Project Structure

```
src/
├── assets/          # Static assets (images, fonts, etc.)
├── components/      # Reusable Vue components
├── views/          # Page components
├── stores/         # Pinia state management
├── utils/          # Utility functions
├── styles/         # Global styles and variables
├── router/         # Vue Router configuration
├── plugins/        # Vue plugins and integrations
├── locales/        # i18n translations
└── types/          # TypeScript type definitions
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build production bundle
- `npm run preview` - Preview production build
- `npm run test` - Run unit tests
- `npm run coverage` - Generate test coverage report
- `npm run lint` - Lint code
- `npm run format` - Format code with Prettier
- `npm run type-check` - Run TypeScript type checking
- `npm run analyze` - Analyze production bundle size

## Development Guidelines

### Code Style

- Follow Vue.js Style Guide (Priority A: Essential)
- Use TypeScript for all new code
- Maintain 100% type safety (strict mode enabled)
- Use composition API with `<script setup>` syntax
- Follow SOLID principles and component design patterns

### Component Guidelines

- Create single-responsibility components
- Use props and events for component communication
- Implement proper prop validation and typing
- Follow atomic design principles for component organization
- Document component API using JSDoc comments

### State Management

- Use Pinia for global state management
- Implement stores using composition API syntax
- Follow store modules pattern for scalability
- Maintain type safety in store definitions
- Use local component state when appropriate

## Testing

### Unit Testing

- Maintain minimum 80% test coverage
- Test all business logic and complex components
- Use Vue Test Utils for component testing
- Follow arrange-act-assert pattern
- Mock external dependencies appropriately

### Testing Commands

```bash
# Run unit tests
npm run test

# Generate coverage report
npm run coverage
```

## Building for Production

### Build Process

1. Update environment variables in `.env.production`
2. Run production build:
```bash
npm run build
```
3. Preview build locally:
```bash
npm run preview
```

### Build Output

Production files will be generated in the `dist` directory with the following structure:

```
dist/
├── assets/
│   ├── js/
│   ├── css/
│   └── images/
└── index.html
```

## Security Guidelines

- Implement Content Security Policy (CSP)
- Sanitize all user inputs
- Use HTTPS for all API communications
- Implement proper authentication flow
- Follow OWASP security best practices
- Regular dependency security audits

## Performance Optimization

- Implement code splitting and lazy loading
- Optimize asset loading and caching
- Use production builds of dependencies
- Implement proper bundle size management
- Regular performance monitoring and optimization

## Accessibility

- Follow WCAG 2.1 AA standards
- Implement proper ARIA attributes
- Ensure keyboard navigation support
- Maintain proper color contrast ratios
- Regular accessibility audits using axe-core

## Internationalization

- Use Vue I18n for translations
- Support right-to-left (RTL) languages
- Implement proper number and date formatting
- Follow ICU message format
- Maintain translation files in JSON format

## Browser Support

- Modern evergreen browsers
- Chrome >= 90
- Firefox >= 90
- Safari >= 14
- Edge >= 90

## Contributing

1. Follow Git branch naming convention
2. Create feature branches from `develop`
3. Submit pull requests with proper descriptions
4. Ensure all tests pass
5. Follow code review process

## License

Private - All rights reserved

## Support

For technical support or questions, please contact the development team.