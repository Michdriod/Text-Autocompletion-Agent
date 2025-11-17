"""
Integration test for KB Article Generation - generates real articles.
Run this to inspect actual article output, structure, and IT tone.
"""
import asyncio
from logic.mode_6 import Mode6


async def test_short_article():
    """Generate a short IT KB article."""
    print("\n" + "="*80)
    print("TEST 1: SHORT ARTICLE (250-450 words)")
    print("="*80)
    
    mode6 = Mode6()
    result = await mode6.generate_article(
        title="Reset MySQL Root Password",
        description="Users need to reset the MySQL root password after forgetting it on Ubuntu 22.04 server running MySQL 8.0.35",
        length="short",
        keywords=["MySQL", "root password", "Ubuntu"],
        output_format="markdown"
    )
    
    print(f"\n📊 METRICS:")
    print(f"   - Total Words: {result['metrics']['total_words']}")
    print(f"   - Target Range: {result['metrics']['word_range']}")
    print(f"   - Complexity: {result['metrics']['complexity']}")
    print(f"   - Coverage: {result['metrics']['keyword_coverage']:.0%}")
    
    print(f"\n📑 SECTIONS: {', '.join(result['sections'].keys())}")
    
    print(f"\n📄 ARTICLE:\n")
    print(result['markdown'])
    print("\n" + "="*80)


async def test_medium_article():
    """Generate a medium IT KB article."""
    print("\n" + "="*80)
    print("TEST 2: MEDIUM ARTICLE (500-900 words)")
    print("="*80)
    
    mode6 = Mode6()
    result = await mode6.generate_article(
        title="Apache SSL Certificate Configuration Error",
        description="Users report ERR_SSL_PROTOCOL_ERROR when accessing Apache 2.4.50 web server after installing new Let's Encrypt SSL certificate on Ubuntu 22.04. The error appears in /var/log/apache2/error.log showing 'SSL Library Error: error:14094410'. Browser displays 'This site can't provide a secure connection' message.",
        length="medium",
        keywords=["Apache", "SSL", "certificate", "ERR_SSL_PROTOCOL_ERROR"],
        output_format="markdown"
    )
    
    print(f"\n📊 METRICS:")
    print(f"   - Total Words: {result['metrics']['total_words']}")
    print(f"   - Target Range: {result['metrics']['word_range']}")
    print(f"   - Complexity: {result['metrics']['complexity']}")
    print(f"   - Coverage: {result['metrics']['keyword_coverage']:.0%}")
    
    print(f"\n📑 SECTIONS: {', '.join(result['sections'].keys())}")
    
    print(f"\n📄 ARTICLE:\n")
    print(result['markdown'])
    print("\n" + "="*80)


async def test_long_article():
    """Generate a long IT KB article with troubleshooting section."""
    print("\n" + "="*80)
    print("TEST 3: LONG ARTICLE (1000-1500 words)")
    print("="*80)
    
    mode6 = Mode6()
    result = await mode6.generate_article(
        title="Database Connection Pool Exhaustion in Production",
        description="Production application experiencing intermittent 'connection pool exhausted' errors on PostgreSQL 14.2 database server. Errors occur during peak load times (1000+ concurrent users). Application log shows 'FATAL: remaining connection slots are reserved' and 'FATAL: sorry, too many clients already'. Database connection pool configured with max_connections=100 in postgresql.conf. Application uses HikariCP connection pool with maximumPoolSize=50 across 3 app servers.",
        length="long",
        keywords=["PostgreSQL", "connection pool", "HikariCP", "max_connections"],
        output_format="markdown"
    )
    
    print(f"\n📊 METRICS:")
    print(f"   - Total Words: {result['metrics']['total_words']}")
    print(f"   - Target Range: {result['metrics']['word_range']}")
    print(f"   - Complexity: {result['metrics']['complexity']}")
    print(f"   - Coverage: {result['metrics']['keyword_coverage']:.0%}")
    
    print(f"\n📑 SECTIONS: {', '.join(result['sections'].keys())}")
    
    print(f"\n📄 ARTICLE:\n")
    print(result['markdown'])
    print("\n" + "="*80)


async def test_very_long_article():
    """Generate a very long IT KB article with all sections."""
    print("\n" + "="*80)
    print("TEST 4: VERY LONG ARTICLE (1500-2500 words)")
    print("="*80)
    
    mode6 = Mode6()
    result = await mode6.generate_article(
        title="Kubernetes Pod Deployment and Troubleshooting Guide",
        description="Comprehensive guide for deploying and troubleshooting Kubernetes pods in production environment running Kubernetes 1.28 on AWS EKS. Covers pod deployment configuration, resource limits, health checks, persistent storage, networking issues, and common failure scenarios. Includes kubectl commands for diagnostics, pod logs inspection, and rollback procedures.",
        length="very_long",
        keywords=["Kubernetes", "pods", "EKS", "deployment", "kubectl"],
        output_format="markdown"
    )
    
    print(f"\n📊 METRICS:")
    print(f"   - Total Words: {result['metrics']['total_words']}")
    print(f"   - Target Range: {result['metrics']['word_range']}")
    print(f"   - Complexity: {result['metrics']['complexity']}")
    print(f"   - Coverage: {result['metrics']['keyword_coverage']:.0%}")
    
    print(f"\n📑 SECTIONS: {', '.join(result['sections'].keys())}")
    
    print(f"\n📄 ARTICLE (first 2000 chars):\n")
    print(result['markdown'][:2000] + "...\n[truncated for display]")
    print("\n" + "="*80)


async def main():
    """Run all integration tests."""
    print("\n🚀 KB ARTICLE GENERATION - INTEGRATION TESTS")
    print("Testing all 4 length options with real AI generation\n")
    
    try:
        await test_short_article()
        await test_medium_article()
        await test_long_article()
        await test_very_long_article()
        
        print("\n✅ ALL INTEGRATION TESTS COMPLETED")
        print("\nVerify:")
        print("  ✓ Article structure matches IT KB format")
        print("  ✓ Sections scale appropriately with length")
        print("  ✓ Technical tone preserved throughout")
        print("  ✓ Keywords appear in generated content")
        print("  ✓ Word counts within target ranges")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
