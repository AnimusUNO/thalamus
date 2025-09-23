# Thalamus Documentation

*This documentation is licensed under [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) (CC BY-SA 4.0).*

Welcome to the Thalamus documentation. This directory contains comprehensive guides and references for understanding and implementing the Thalamus cognitive architecture.

## 📚 Documentation Overview

### Core Documentation
- **[Main README](../README.md)** - The Thalamus whitepaper and primary documentation
- **[Technical Reference](TECHNICAL_REFERENCE.md)** - Implementation details, database schema, and API reference
- **[Demo Guide](DEMO_GUIDE.md)** - How to run and improve the Thalamus demos
- **[OMI Webhook Guide](OMI_WEBHOOK_GUIDE.md)** - Webhook integration and real-time data processing
- **[Changelog](CHANGELOG.md)** - Version history and release notes

## 🚀 Quick Start

### For Researchers
1. **Read the [Main README](../README.md)** - Start with the whitepaper to understand the cognitive architecture
2. **Run the [Forensiq Demo](../examples/forensiq_demo/)** - Interactive TUI demonstration
3. **Explore the [Technical Reference](TECHNICAL_REFERENCE.md)** - Implementation details

### For Developers
1. **Review the [Technical Reference](TECHNICAL_REFERENCE.md)** - Database schema and API details
2. **Follow the [Demo Guide](DEMO_GUIDE.md)** - Set up and run the reference implementations
3. **Integrate with [OMI Webhook Guide](OMI_WEBHOOK_GUIDE.md)** - Real-time data processing

### For Integrators
1. **Study the [OMI Webhook Guide](OMI_WEBHOOK_GUIDE.md)** - Webhook integration patterns
2. **Reference the [Technical Reference](TECHNICAL_REFERENCE.md)** - API and data formats
3. **Test with [Demo Guide](DEMO_GUIDE.md)** - Validate your integration

## 📖 Documentation Structure

```
docs/
├── README.md                    # This navigation index
├── TECHNICAL_REFERENCE.md       # Implementation details & API reference
├── DEMO_GUIDE.md               # Demo instructions & improvements
├── OMI_WEBHOOK_GUIDE.md        # Webhook integration guide
└── CHANGELOG.md                # Version history
```

## 🎯 What is Thalamus?

Thalamus is a middleware architecture for agentic AI systems that balances low-latency reflexive processing with parallel refinement of perceptual streams. Inspired by biological thalamic function, it enables raw sensory input to be routed immediately to reflex-level subsystems while preparing cleaned and annotated versions in parallel.

### Key Concepts
- **Parallel Processing**: Raw input processed immediately while refined versions prepared in parallel
- **Reflex vs. Depth**: Fast reflex responses vs. deeper cognitive processing
- **Flow Control**: Explicit escalation from reflex to higher-order cognition
- **Provenance Tracking**: Complete audit trail from raw input to refined output

## 🔧 Implementation Examples

### Reference Architecture
The `examples/` directory contains complete reference implementations:

- **[Forensiq Demo](../examples/forensiq_demo/)** - Interactive TUI showing cognitive architecture
- **[Data Ingestion](../examples/thalamus_app.py)** - Real-time speech-to-text processing
- **[Transcript Refinement](../examples/transcript_refiner.py)** - AI-powered text enhancement
- **[Webhook Server](../examples/omi_webhook.py)** - Real-time data endpoint

### Database Schema
Thalamus uses SQLite with five main tables:
- `sessions` - Session management
- `speakers` - Speaker identification
- `raw_segments` - Original speech-to-text data
- `refined_segments` - AI-enhanced transcripts
- `segment_usage` - Processing provenance tracking

## 🤝 Contributing

### Documentation
- Follow the existing structure and style
- Update this index when adding new documentation
- Include practical examples and code snippets
- Cross-reference related sections

### Code
- Reference implementations in `examples/`
- Follow the patterns established in the technical reference
- Include comprehensive error handling
- Document API changes in the changelog

## 📞 Support

For questions about:
- **Research concepts**: See the [Main README](../README.md)
- **Implementation details**: Check the [Technical Reference](TECHNICAL_REFERENCE.md)
- **Running demos**: Follow the [Demo Guide](DEMO_GUIDE.md)
- **Integration issues**: Review the [OMI Webhook Guide](OMI_WEBHOOK_GUIDE.md)

## 🔗 External Resources

- **AnimusOS**: The broader middleware ecosystem
- **Cochlea Schema**: JSON event format specification
- **OpenAI API**: AI text refinement capabilities
- **Textual**: TUI framework for the Forensiq demo

---

*This documentation is maintained as part of the Thalamus project. For the latest updates, see the [Changelog](CHANGELOG.md).*
