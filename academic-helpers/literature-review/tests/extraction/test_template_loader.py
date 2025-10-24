# tests/extraction/test_template_loader.py
import pytest
from extraction.template_loader import TemplateLoader

def test_load_observational_template():
    """Test loading observational study template."""
    loader = TemplateLoader()
    template = loader.load_template('observational_study')

    assert template is not None
    assert template['name'] == 'Observational Study'
    assert 'fields' in template
    assert 'study_design' in template['fields']

def test_template_field_structure():
    """Test template field has required attributes."""
    loader = TemplateLoader()
    template = loader.load_template('observational_study')

    study_design = template['fields']['study_design']

    assert 'type' in study_design
    assert 'prompt' in study_design
    assert study_design['type'] == 'select'
    assert 'options' in study_design

def test_list_templates():
    """Test listing all available templates."""
    loader = TemplateLoader()
    templates = loader.list_templates()

    assert 'observational_study' in templates
    assert 'spatial_analysis' in templates
    assert 'qualitative_study' in templates
