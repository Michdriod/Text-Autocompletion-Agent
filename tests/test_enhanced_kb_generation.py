"""
Tests for enhanced KB Article Generation (Mode 6) with length selection.
Tests length ranges, section inclusion, validation suggestions, and IT tone preservation.
"""
import pytest
from services.input_validation import validate_kb_inputs
from services.context_extraction import extract_context
from services.article_planner import plan_article_length
from config.settings import LENGTH_RANGES, SECTIONS_BY_LENGTH


class TestLengthSelection:
    """Test user-selectable length ranges."""
    
    def test_short_length_range(self):
        """Short articles should be 250-450 words."""
        context = {
            'complexity': 'procedural',
            'complexity_multiplier': 1.0,
            'keywords': []
        }
        plan = plan_article_length('short', context)
        
        assert plan['length_choice'] == 'short'
        assert 250 <= plan['total_target_words'] <= 450
        assert plan['word_range'] == (250, 450)
    
    def test_medium_length_range(self):
        """Medium articles should be 500-900 words."""
        context = {
            'complexity': 'procedural',
            'complexity_multiplier': 1.0,
            'keywords': []
        }
        plan = plan_article_length('medium', context)
        
        assert plan['length_choice'] == 'medium'
        assert 500 <= plan['total_target_words'] <= 900
        assert plan['word_range'] == (500, 900)
    
    def test_long_length_range(self):
        """Long articles should be 1000-1500 words."""
        context = {
            'complexity': 'troubleshooting',
            'complexity_multiplier': 1.05,
            'keywords': []
        }
        plan = plan_article_length('long', context)
        
        assert plan['length_choice'] == 'long'
        assert 1000 <= plan['total_target_words'] <= 1500
        assert plan['word_range'] == (1000, 1500)
    
    def test_very_long_length_range(self):
        """Very long articles should be 1500-2500 words."""
        context = {
            'complexity': 'procedural',
            'complexity_multiplier': 1.0,
            'keywords': []
        }
        plan = plan_article_length('very_long', context)
        
        assert plan['length_choice'] == 'very_long'
        assert 1500 <= plan['total_target_words'] <= 2500
        assert plan['word_range'] == (1500, 2500)


class TestSectionInclusion:
    """Test section inclusion based on length choice."""
    
    def test_short_sections(self):
        """Short articles should have minimal sections."""
        context = {'complexity': 'simple', 'complexity_multiplier': 0.95, 'keywords': []}
        plan = plan_article_length('short', context)
        
        assert set(plan['sections']) == {'purpose', 'steps', 'validation'}
        assert 'symptoms' not in plan['sections']
        assert 'notes' not in plan['sections']
    
    def test_medium_sections(self):
        """Medium articles should have standard IT KB sections."""
        context = {'complexity': 'procedural', 'complexity_multiplier': 1.0, 'keywords': []}
        plan = plan_article_length('medium', context)
        
        assert set(plan['sections']) == {'purpose', 'symptoms', 'steps', 'validation', 'notes'}
    
    def test_long_sections(self):
        """Long articles should include troubleshooting."""
        context = {'complexity': 'troubleshooting', 'complexity_multiplier': 1.05, 'keywords': []}
        plan = plan_article_length('long', context)
        
        expected = {'purpose', 'symptoms', 'steps', 'validation', 'troubleshooting', 'notes'}
        assert set(plan['sections']) == expected
    
    def test_very_long_sections(self):
        """Very long articles should include all optional sections."""
        context = {'complexity': 'procedural', 'complexity_multiplier': 1.0, 'keywords': []}
        plan = plan_article_length('very_long', context)
        
        expected = {
            'prerequisites', 'purpose', 'symptoms', 'steps', 
            'validation', 'troubleshooting', 'notes', 
            'best_practices', 'faq'
        }
        assert set(plan['sections']) == expected


class TestSectionAllocation:
    """Test word allocation to sections."""
    
    def test_steps_largest_section(self):
        """Steps should always be the largest section (IT focus)."""
        context = {'complexity': 'procedural', 'complexity_multiplier': 1.0, 'keywords': []}
        plan = plan_article_length('medium', context)
        
        allocation = plan['allocation']
        assert allocation['steps'] == max(allocation.values())
    
    def test_allocation_sum_matches_target(self):
        """Sum of allocations should match total target (within residual tolerance)."""
        context = {'complexity': 'troubleshooting', 'complexity_multiplier': 1.05, 'keywords': []}
        plan = plan_article_length('long', context)
        
        # Allow small residual difference due to rounding and redistribution limits
        diff = abs(sum(plan['allocation'].values()) - plan['total_target_words'])
        assert diff <= 20, f"Allocation sum difference too large: {diff}"
    
    def test_section_floors_respected(self):
        """All sections should meet minimum floor requirements."""
        from config.settings import SECTION_MIN_FLOORS
        
        context = {'complexity': 'simple', 'complexity_multiplier': 0.95, 'keywords': []}
        plan = plan_article_length('short', context)
        
        for section, words in plan['allocation'].items():
            floor = SECTION_MIN_FLOORS.get(section, 50)
            assert words >= floor, f"{section} has {words} words but floor is {floor}"


class TestValidationSuggestions:
    """Test validation provides helpful suggestions instead of rejecting."""
    
    def test_short_title_suggestions(self):
        """Short title should return suggestions."""
        result = validate_kb_inputs("SSL", "Users experiencing timeout when accessing SSL admin panel on Apache 2.4 server", "medium")
        
        assert not result['valid']
        assert 'Title too short' in result['issues']
        assert any('descriptive title' in s.lower() for s in result['suggestions'])
    
    def test_short_description_suggestions(self):
        """Short description should return suggestions."""
        result = validate_kb_inputs(
            "SSL Configuration Issue", 
            "Users have problems",  # Only 3 words
            "medium"
        )
        
        assert not result['valid']
        assert any('too short' in issue.lower() for issue in result['issues'])
        assert any('specific details' in s.lower() for s in result['suggestions'])
    
    def test_vague_description_suggestions(self):
        """Vague description should return IT-specific suggestions."""
        vague_desc = "There is a problem with the system and users cannot do things properly in the application"
        result = validate_kb_inputs("System Problem", vague_desc, "medium")
        
        assert not result['valid']
        assert 'too generic' in result['issues'][0].lower()
        assert any('system' in s.lower() or 'version' in s.lower() for s in result['suggestions'])
    
    def test_invalid_length_suggestions(self):
        """Invalid length choice should suggest valid options."""
        result = validate_kb_inputs(
            "Apache SSL Configuration",
            "Users experiencing connection timeout errors when accessing Apache admin panel with SSL certificate",
            "extra_huge"  # Invalid
        )
        
        assert not result['valid']
        assert any('invalid length' in issue.lower() for issue in result['issues'])
        assert any('short' in s or 'medium' in s for s in result['suggestions'])
    
    def test_valid_input_no_suggestions(self):
        """Valid input should pass without suggestions."""
        result = validate_kb_inputs(
            "Apache SSL Certificate Timeout Error",
            "Users experience connection timeout error (ERR_CONNECTION_TIMED_OUT) when accessing Apache 2.4.50 admin panel after installing new SSL certificate from Let's Encrypt",
            "medium",
            ["Apache", "SSL", "timeout"]
        )
        
        assert result['valid']
        assert 'suggestions' not in result


class TestComplexityAdjustment:
    """Test complexity multiplier for fine-tuning."""
    
    def test_simple_reduces_length(self):
        """Simple complexity should slightly reduce target length."""
        context_simple = {'complexity': 'simple', 'complexity_multiplier': 0.95, 'keywords': []}
        context_normal = {'complexity': 'procedural', 'complexity_multiplier': 1.0, 'keywords': []}
        
        plan_simple = plan_article_length('medium', context_simple)
        plan_normal = plan_article_length('medium', context_normal)
        
        assert plan_simple['total_target_words'] <= plan_normal['total_target_words']
    
    def test_troubleshooting_increases_length(self):
        """Troubleshooting complexity should slightly increase target length."""
        context_normal = {'complexity': 'procedural', 'complexity_multiplier': 1.0, 'keywords': []}
        context_troubleshoot = {'complexity': 'troubleshooting', 'complexity_multiplier': 1.05, 'keywords': []}
        
        plan_normal = plan_article_length('medium', context_normal)
        plan_troubleshoot = plan_article_length('medium', context_troubleshoot)
        
        assert plan_troubleshoot['total_target_words'] >= plan_normal['total_target_words']


class TestContextExtraction:
    """Test context extraction maintains IT focus."""
    
    def test_troubleshooting_keywords_detected(self):
        """Should detect troubleshooting keywords."""
        from services.context_extraction import classify_complexity
        
        desc = "Database connection timeout error occurs when users login"
        complexity, multiplier = classify_complexity(desc)
        
        assert complexity == 'troubleshooting'
        assert multiplier > 1.0  # Should be higher for troubleshooting
    
    def test_procedural_keywords_detected(self):
        """Should detect procedural keywords."""
        from services.context_extraction import classify_complexity
        
        desc = "Install and configure Apache SSL certificate on Ubuntu server"
        complexity, multiplier = classify_complexity(desc)
        
        assert complexity == 'procedural'
        assert multiplier >= 1.0  # Should be 1.0 or higher for procedural
    
    def test_entity_extraction_technical_terms(self):
        """Should extract technical entities from description."""
        desc = "Apache 2.4.50 server shows ERR_SSL_PROTOCOL_ERROR on /var/log/apache2/error.log after upgrading to Ubuntu 22.04"
        context = extract_context(desc, None)
        
        entities = context['entities']
        assert len(entities['versions']) > 0  # Should find version numbers
        assert len(entities['paths']) > 0     # Should find file paths
        # Error codes detection is optional - just check entity count
        assert context['entity_count'] >= 3  # At least paths + versions


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
