"""
Test optimized Mode 6 with diverse article types
"""
from logic.mode_6_sectional import Mode6Sectional
import asyncio
import time

test_cases = [
    {
        'name': 'API Integration Guide',
        'title': 'Integrating REST APIs with OAuth 2.0',
        'description': 'A comprehensive guide on integrating third-party REST APIs using OAuth 2.0 authentication, including token management and error handling',
        'keywords': ['REST API', 'OAuth 2.0', 'authentication', 'token', 'integration', 'API security'],
        'length': 'long',
        'audience': 'software developers'
    },
    {
        'name': 'Troubleshooting Network Issues',
        'title': 'Troubleshooting Common Network Connectivity Issues',
        'description': 'Step-by-step guide to diagnose and resolve network connectivity problems including DNS issues, firewall blocking, and routing problems',
        'keywords': ['network', 'troubleshooting', 'DNS', 'firewall', 'connectivity', 'ping', 'traceroute'],
        'length': 'medium',
        'audience': 'IT support staff'
    },
    {
        'name': 'Database Migration',
        'title': 'Migrating from MySQL to PostgreSQL',
        'description': 'Complete migration guide covering schema conversion, data transfer, application updates, and post-migration validation',
        'keywords': ['database migration', 'MySQL', 'PostgreSQL', 'data transfer', 'schema conversion'],
        'length': 'very_long',
        'audience': 'database administrators'
    },
    {
        'name': 'Password Security Policy',
        'title': 'Implementing Strong Password Policies',
        'description': 'Best practices for creating and enforcing password policies including complexity requirements, expiration rules, and multi-factor authentication',
        'keywords': ['password security', 'policy', 'MFA', 'authentication', 'compliance'],
        'length': 'short',
        'audience': 'security administrators'
    }
]

async def run_tests():
    print('🧪 Testing optimized Mode 6 with diverse examples...')
    print('=' * 60)
    
    mode6 = Mode6Sectional()
    
    for i, test in enumerate(test_cases, 1):
        print(f'\n📋 Test Case {i}: {test["name"]}')
        print(f'Title: {test["title"]}')
        print(f'Length: {test["length"]}')
        print(f'Keywords: {", ".join(test["keywords"][:4])}...')
        print('-' * 40)
        
        start = time.time()
        try:
            article = await mode6.generate_article(
                title=test['title'],
                description=test['description'],
                keywords=test['keywords'],
                length_mode=test['length'],
                audience=test.get('audience')
            )
            elapsed = time.time() - start
            
            word_count = len(article.split())
            print(f'✅ Generation successful!')
            print(f'📊 Words: {word_count}')
            print(f'⏱️  Time: {elapsed:.2f}s')
            print(f'\n📄 Preview (first 400 chars):')
            print('-' * 40)
            print(article[:400] + '...')
            
            # Save to file
            filename = f"test_output_{i}_{test['name'].lower().replace(' ', '_')}.md"
            with open(filename, 'w') as f:
                f.write(article)
            print(f'💾 Full article saved to: {filename}')
            
        except Exception as e:
            elapsed = time.time() - start
            print(f'❌ Generation failed after {elapsed:.2f}s')
            print(f'Error: {str(e)}')
    
    print('\n' + '=' * 60)
    print('🎉 All tests completed!')

if __name__ == '__main__':
    asyncio.run(run_tests())
