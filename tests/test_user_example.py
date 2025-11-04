#!/usr/bin/env python3

"""Test Mode 5 with the exact example from the user request."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/mac/Text-Autocompletion-Agent')

from logic.mode_5 import Mode5

# Exact text from user request
user_example_text = """API Integration: The Digital Handshake Powering Modern Connectivity

In today's interconnected digital world, few technologies are as essential yet as invisible as API integration. Behind every seamless online experience—ordering food from an app, tracking a package in real time, or signing in with Google—there's an Application Programming Interface, or API, quietly orchestrating the exchange of data between systems. APIs are the unseen bridges of the digital age, enabling businesses and users to connect across platforms effortlessly.

At its core, API integration refers to the process of linking two or more software applications through their APIs so they can communicate, share data, and perform coordinated functions. Think of it as a digital handshake between systems—an agreement that defines how information should be exchanged, what rules govern that exchange, and what each side can expect in return. Without APIs, each software system would remain isolated, forcing developers to build direct, complex connections for every new feature or service. With APIs, systems can plug into one another easily, creating an ecosystem of reusable and extendable digital capabilities.

How APIs Work

An API serves as a messenger or translator. When one system sends a request—such as asking for user information or product details—the API translates that request into a format the receiving system understands. It then returns the response in a standardized way. For example, when you use a travel app to find flights, the app doesn't own flight data—it queries airline APIs, which respond with live flight schedules and prices.

Most modern systems rely on RESTful APIs (Representational State Transfer). REST uses standard HTTP methods—like GET, POST, PUT, and DELETE—to interact with resources. Data is typically exchanged in JSON (JavaScript Object Notation), a lightweight and readable format that makes integration faster and easier. REST APIs are stateless, meaning each request is processed independently without relying on previous ones, which improves scalability and reliability.

The Strategic Value of API Integration

The impact of API integration goes beyond technical convenience—it's now a cornerstone of business strategy. By linking systems, organizations can achieve automation, innovation, and scalability that were once impossible.

Automation and Efficiency
APIs remove the need for repetitive manual data transfers. When an e-commerce platform integrates its order system with a shipping provider's API, shipping details update automatically the moment an order is placed. This eliminates manual entry errors and saves time across departments.

Innovation Through Reuse
Instead of reinventing the wheel, developers can build on existing services. For instance, fintech apps leverage banking APIs for secure transactions; location-based services use mapping APIs like Google Maps; and chatbots integrate with messaging APIs to communicate across platforms. By combining APIs, teams can innovate faster, focusing on value rather than infrastructure.

Scalability and Growth
APIs allow businesses to scale effortlessly. Cloud-based systems can connect multiple tools—CRM, analytics, marketing automation—so that as the business grows, data flows seamlessly across all operations. This connectedness helps organizations stay agile and responsive in changing markets.

Ecosystem Expansion
APIs also create opportunities for partnerships. Companies can expose their APIs to external developers, fostering ecosystems of innovation. For example, payment companies like Stripe or PayPal have built entire developer communities that extend their reach globally through API-based integrations.

Security, Reliability, and Best Practices

While APIs open doors to connectivity, they also introduce new responsibilities. Security is paramount. APIs must authenticate requests—typically through mechanisms like OAuth 2.0 or API keys—to ensure that only authorized users or systems can access data. Encryption through HTTPS protects data in transit, while rate limiting prevents systems from being overwhelmed by excessive requests.

Equally important is error handling and stability. A poorly managed API can cause cascading failures across dependent systems. Developers implement retry logic, timeout limits, and descriptive error responses to maintain system reliability. Monitoring and analytics tools also track API performance and uptime to quickly detect anomalies.

Real-World Applications

From consumer technology to enterprise systems, API integration drives countless daily interactions.

Social Media: "Log in with Facebook" or "Share on Twitter" buttons are powered by authentication and content-sharing APIs.

Finance: Banking APIs enable secure account connections for budgeting apps and digital payments.

Healthcare: APIs connect patient management systems, allowing hospitals to access lab results and medical histories securely.

Logistics: Delivery companies use APIs to update tracking data in real time across customer portals.

In all these examples, APIs are not just connectors—they're catalysts that redefine user experience and operational speed.

The Future of API Integration

As businesses continue to digitize, the demand for API connectivity is only accelerating. The rise of microservices, cloud computing, and AI-driven workflows depends on seamless API communication. Meanwhile, GraphQL, an alternative to REST, is gaining popularity for giving clients more control over the data they request.

In the long term, APIs will form the foundation of digital ecosystems—where every service, from analytics to automation, communicates through shared interfaces. The organizations that master API integration will be the ones best equipped to innovate, adapt, and scale in a connected world."""

async def test_user_example():
    """Test with the exact user example."""
    print("🧪 Testing User Example - API Integration Document")
    print("=" * 70)
    
    mode5 = Mode5()
    
    # Test with different word counts to show professional formatting
    test_cases = [
        {"words": 100, "name": "Short Professional Summary"},
        {"words": 200, "name": "Medium Professional Summary"},
        {"words": 400, "name": "Comprehensive Professional Summary"}
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {case['name']} ({case['words']} words)")
        print("-" * 60)
        
        result = await mode5.process_raw_text(
            text=user_example_text,
            source_name="user_api_example",
            target_words=case['words'],
            output_format="markdown"
        )
        
        print(f"Target: {case['words']} words")
        print(f"Actual: {result['summary_words']} words")
        deviation = abs(result['summary_words'] - case['words']) / case['words'] * 100
        print(f"Deviation: {deviation:.1f}%")
        
        print(f"\n📄 Summary Output:")
        print(result['markdown_summary'])
        print("\n" + "="*70)
    
    # Test document without title
    print("\n📝 Test 4: Document Without Title")
    print("-" * 60)
    
    no_title_text = """Cloud computing has fundamentally transformed how businesses operate in the digital age. Organizations can now access computing resources on-demand, scaling infrastructure up or down based on immediate needs. This flexibility reduces operational costs while improving efficiency across all business functions. The three primary service models—Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS)—offer varying levels of control and abstraction. As digital transformation accelerates, cloud computing becomes increasingly critical for maintaining competitive advantage."""
    
    result4 = await mode5.process_raw_text(
        text=no_title_text,
        source_name="no_title_example",
        target_words=80,
        output_format="markdown"
    )
    
    print(f"Target: 80 words")
    print(f"Actual: {result4['summary_words']} words")
    deviation4 = abs(result4['summary_words'] - 80) / 80 * 100
    print(f"Deviation: {deviation4:.1f}%")
    
    print(f"\n📄 Summary Output:")
    print(result4['markdown_summary'])

if __name__ == "__main__":
    asyncio.run(test_user_example())