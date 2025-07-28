# AI Integration Development Guidelines

## Overview

This steering document provides guidelines for integrating multiple AI coding agent implementations in the PhotoGeoView project. It establishes standards for maintaining code quality, consistency, and collaboration between GitHub Copilot, Cursor, and Kiro implementations.

## AI Role Definitions

### GitHub Copilot (CS4Coding)
- **Primary Focus**: Core functionality implementation
- **Strengths**: Code completion, pattern recognition, stable implementations
- **Responsibilities**: EXIF parsing, image processing, map integration, error handling

### Cursor (CursorBLD)
- **Primary Focus**: UI/UX design and user experience
- **Strengths**: Interface design, theme systems, real-time editing
- **Responsibilities**: Main window layout, theme management, thumbnail display, navigation

### Kiro
- **Primary Focus**: Architecture integration and quality assurance
- **Strengths**: Project structure, cross-component integration, testing
- **Responsibilities**: Overall architecture, performance optimization, testing strategy, documentation

## Integration Principles

### Code Organization
- Maintain clear attribution of AI contributions in file headers
- Use consistent naming conventions across all AI implementations
- Implement unified error handling and logging systems
- Ensure modular design with clear interfaces between components

### Quality Standards
- All integrated code must pass comprehensive testing
- Performance benchmarks must meet or exceed individual AI implementations
- Documentation must be maintained for all integrated components
- Code reviews should consider multi-AI compatibility

### Development Workflow
1. **Requirements Phase**: Kiro leads with input from all AIs
2. **Design Phase**: Collaborative design with AI-specific focus areas
3. **Implementation Phase**: Parallel development with integration checkpoints
4. **Testing Phase**: Comprehensive integration testing
5. **Deployment Phase**: Coordinated release with monitoring

## Technical Standards

### Dependencies
- Use unified dependency management (requirements.txt)
- Prefer libraries that work well across all AI implementations
- Document any AI-specific dependency requirements
- Maintain backward compatibility where possible

### Configuration
- Centralized configuration management
- Environment-specific settings support
- AI-specific configuration sections where needed
- User preference persistence across AI components

### Performance
- Memory usage optimization across all components
- Efficient caching strategies for shared resources
- Asynchronous processing where appropriate
- Regular performance monitoring and optimization

## Testing Strategy

### Integration Testing
- Test AI component interactions
- Verify unified user experience
- Performance regression testing
- Cross-platform compatibility testing

### Quality Assurance
- Automated code quality checks
- Documentation completeness verification
- Security vulnerability scanning
- Accessibility compliance testing

## Documentation Requirements

### Code Documentation
- Clear docstrings for all public interfaces
- AI contribution attribution in file headers
- Architecture decision records for integration choices
- API documentation for inter-component communication

### User Documentation
- Unified user manual covering all features
- Installation and setup guides
- Troubleshooting documentation
- Feature comparison with individual AI versions

## Collaboration Guidelines

### Communication
- Regular integration status updates
- Clear issue reporting and tracking
- Collaborative problem-solving approach
- Knowledge sharing between AI implementations

### Conflict Resolution
- Kiro mediates technical disagreements
- Performance benchmarks guide implementation choices
- User experience takes priority in UI decisions
- Maintainability considerations for long-term decisions
