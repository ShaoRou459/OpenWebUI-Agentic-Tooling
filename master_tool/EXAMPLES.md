# Agentic Master Tool - Usage Examples

This document provides real-world examples of how to use the Agentic Master Tool.

## Table of Contents

1. [Basic Web Search](#basic-web-search)
2. [Advanced Research](#advanced-research)
3. [Code Execution](#code-execution)
4. [Image Generation](#image-generation)
5. [Combined Workflows](#combined-workflows)

---

## Basic Web Search

### Quick News Search

```
User: What's the latest news about AI?

AI: Let me search for the latest AI news.

[Internally calls: web_search(query="latest AI news 2025", mode="STANDARD")]

Based on current sources, here are the latest developments in AI:

1. **OpenAI Releases GPT-5** - OpenAI announced GPT-5 with improved reasoning...
2. **Google DeepMind Breakthrough** - New protein folding capabilities...
3. **AI Regulation Updates** - EU AI Act implementation timeline...

[Sources shown if web_search_show_sources=true]
```

### Reading a Specific Article

```
User: Can you read and summarize this article? https://example.com/ai-breakthrough

AI: I'll read that article for you.

[Internally calls: web_search(query="https://example.com/ai-breakthrough", mode="CRAWL")]

This article discusses a breakthrough in AI reasoning. Key points:
- New architecture improves logical reasoning by 40%
- Reduced hallucinations through better grounding
- Applications in scientific research and education
```

### Comparing Search Modes

**STANDARD Mode** (Fast, most common):
```
Query: "What is quantum computing?"
Time: ~5-10 seconds
Sources: 3-5 URLs
Best for: Quick facts, recent news, straightforward questions
```

**COMPLETE Mode** (Deep research):
```
Query: "Comprehensive analysis of quantum computing's impact on cryptography"
Time: ~30-60 seconds
Sources: 10-15 URLs across multiple iterations
Best for: Complex topics, comprehensive research, academic questions
```

---

## Advanced Research

### Multi-iteration Research

```
User: I need a comprehensive analysis of renewable energy trends, market dynamics, and future predictions.

AI: This requires deep research. I'll use the COMPLETE mode to gather comprehensive information.

[Internally calls: web_search(query="comprehensive analysis of renewable energy trends market dynamics future predictions", mode="COMPLETE")]

# Comprehensive Analysis of Renewable Energy Trends

## Market Dynamics
Based on research across 12 sources...

## Current Trends
The renewable energy sector is experiencing...

## Future Predictions
Industry experts project...

## Investment Opportunities
Key areas for investment include...
```

### Targeted URL Crawling

```
User: Read these three research papers and summarize their key findings:
- https://paper1.com
- https://paper2.com
- https://paper3.com

AI: I'll read each paper and provide a comparative summary.

[Calls web_search three times with mode="CRAWL"]

# Comparative Analysis

## Paper 1: [Title]
Key Findings:
- Finding 1...
- Finding 2...

## Paper 2: [Title]
Key Findings:
- Finding 1...
- Finding 2...

## Paper 3: [Title]
Key Findings:
- Finding 1...
- Finding 2...

## Synthesis
Across all three papers, the common themes are...
```

---

## Code Execution

### Data Analysis Workflow

```
User: I have sales data. Can you analyze it and create visualizations?

AI: I'll enable the code interpreter to analyze your data.

[Internally calls: code_interpreter(enable=True, use_jupyter=True)]

Perfect! I can now execute Python code. Please upload your CSV file, and I'll analyze it.

User: [Uploads sales_data.csv]

AI: Let me analyze this data.

<code_interpreter type="code" lang="python">
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read the data
df = pd.read_csv('/work/sales_data.csv')

# Basic statistics
print("Dataset Overview:")
print(df.describe())
print("\n" + "="*50 + "\n")

# Sales by month
monthly_sales = df.groupby('month')['revenue'].sum()
print("Monthly Sales:")
print(monthly_sales)

# Create visualization
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
monthly_sales.plot(kind='bar', color='steelblue')
plt.title('Monthly Sales Revenue')
plt.xlabel('Month')
plt.ylabel('Revenue ($)')

plt.subplot(1, 2, 2)
top_products = df.groupby('product')['revenue'].sum().nlargest(10)
top_products.plot(kind='barh', color='coral')
plt.title('Top 10 Products by Revenue')

plt.tight_layout()
plt.savefig('/work/sales_analysis.png', dpi=300, bbox_inches='tight')
print("\n✓ Analysis complete! Chart saved.")

# Upload the chart
import uploader
link = uploader.upload_file('/work/sales_analysis.png')
print(f"\nChart URL: {link}")
</code_interpreter>

Based on the analysis:

**Key Insights:**
- Total revenue: $1.2M
- Best performing month: December ($350K)
- Top product: Product A ($180K)
- Growth trend: +15% month-over-month

**Visualization:**
![Sales Analysis](uploaded-image-url)

**Recommendations:**
1. Focus marketing on top-performing products
2. Investigate December spike for replication
3. Address underperforming product lines
```

### Scientific Computing

```
User: Calculate the trajectory of a projectile with initial velocity 50 m/s at 45 degrees

AI: I'll use Python to calculate and visualize the projectile motion.

[Calls: code_interpreter(enable=True)]

<code_interpreter type="code" lang="python">
import numpy as np
import matplotlib.pyplot as plt

# Constants
g = 9.81  # m/s^2
v0 = 50   # m/s
theta = 45 * np.pi / 180  # Convert to radians

# Calculate trajectory
t_max = 2 * v0 * np.sin(theta) / g
t = np.linspace(0, t_max, 100)

x = v0 * np.cos(theta) * t
y = v0 * np.sin(theta) * t - 0.5 * g * t**2

# Key values
max_height = (v0 * np.sin(theta))**2 / (2 * g)
total_range = v0**2 * np.sin(2 * theta) / g
time_to_max = v0 * np.sin(theta) / g

print(f"Maximum Height: {max_height:.2f} m")
print(f"Total Range: {total_range:.2f} m")
print(f"Time to Max Height: {time_to_max:.2f} s")
print(f"Total Flight Time: {t_max:.2f} s")

# Plot
plt.figure(figsize=(10, 6))
plt.plot(x, y, 'b-', linewidth=2)
plt.plot([0, total_range], [0, 0], 'k--', alpha=0.3)
plt.plot([total_range/2], [max_height], 'ro', markersize=10)
plt.xlabel('Horizontal Distance (m)')
plt.ylabel('Vertical Height (m)')
plt.title('Projectile Trajectory')
plt.grid(True, alpha=0.3)
plt.savefig('trajectory.png')
print("\n✓ Trajectory plotted!")
</code_interpreter>

**Results:**
- Maximum Height: 63.78 m
- Total Range: 254.84 m
- Flight Time: 7.21 s
```

---

## Image Generation

### Creating Marketing Materials

```
User: Create an image for our new eco-friendly product line

AI: I'll generate a professional image for your eco-friendly product line.

[Calls: image_generation(
    prompt="Professional product photography style image showing eco-friendly products: bamboo toothbrush, reusable water bottle, organic cotton bag, wooden utensils, all arranged aesthetically on a clean white surface with natural lighting and green plant accents",
    description="Eco-friendly product collection"
)]

![Eco-friendly product collection](generated-image-url)

*Eco-friendly product collection*

I've created a clean, professional image showcasing your eco-friendly products. The natural lighting and plant accents emphasize the environmental focus. Would you like me to generate variations or create additional marketing materials?
```

### Technical Diagrams

```
User: Create a diagram showing how a neural network processes data

AI: I'll generate a clear technical diagram of neural network data processing.

[Calls: image_generation(
    prompt="Clean technical diagram illustration of a neural network architecture showing input layer with 4 nodes, two hidden layers with 6 nodes each, and output layer with 2 nodes, with arrows showing data flow, labels for each layer, and a clean white background with blue and orange accent colors",
    description="Neural Network Architecture Diagram"
)]

![Neural Network Architecture Diagram](generated-image-url)

*Neural Network Architecture Diagram*

This diagram illustrates the basic structure of a feedforward neural network with:
- Input Layer (4 features)
- Hidden Layers (2 layers, 6 neurons each)
- Output Layer (2 classes)
- Forward propagation flow
```

---

## Combined Workflows

### Research → Analysis → Visualization

```
User: Research the stock market performance of tech companies in 2024, then analyze trends

AI: I'll conduct comprehensive research and then analyze the data.

**Step 1: Research**

[Calls: web_search(
    query="tech company stock market performance 2024 comprehensive analysis",
    mode="COMPLETE"
)]

I've gathered data on major tech companies' 2024 performance:
- Apple: +23%
- Microsoft: +31%
- Google: +18%
- Amazon: +28%
- Meta: +42%

**Step 2: Enable Code Analysis**

[Calls: code_interpreter(enable=True, use_jupyter=True)]

**Step 3: Analyze & Visualize**

<code_interpreter type="code" lang="python">
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Data from research
companies = ['Apple', 'Microsoft', 'Google', 'Amazon', 'Meta']
performance = [23, 31, 18, 28, 42]

# Create visualization
plt.figure(figsize=(10, 6))
colors = sns.color_palette("husl", len(companies))
bars = plt.bar(companies, performance, color=colors)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'+{height}%',
             ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.title('Tech Company Stock Performance 2024', fontsize=16, fontweight='bold')
plt.ylabel('Growth (%)', fontsize=12)
plt.xlabel('Company', fontsize=12)
plt.ylim(0, 50)
plt.grid(axis='y', alpha=0.3)

# Add average line
avg_performance = sum(performance) / len(performance)
plt.axhline(y=avg_performance, color='red', linestyle='--',
            label=f'Average: {avg_performance:.1f}%')
plt.legend()

plt.tight_layout()
plt.savefig('tech_performance_2024.png', dpi=300)
print(f"Average growth: {avg_performance:.1f}%")
print(f"Best performer: {companies[performance.index(max(performance))]} ({max(performance)}%)")
print(f"Range: {max(performance) - min(performance)}%")
</code_interpreter>

**Analysis Results:**
- Average Growth: 28.4%
- Best Performer: Meta (+42%)
- Most Volatile: Meta vs Google spread (24% difference)
- Sector Overall: Strong bullish trend

**Key Insights:**
1. Meta's transformation and AI investments drove exceptional returns
2. Microsoft benefited from cloud and AI integration
3. Google lagged due to AI competition concerns
4. All companies showed positive growth despite market headwinds
```

### Content Creation Pipeline

```
User: Create a blog post about sustainable living with images

AI: I'll create a comprehensive blog post with supporting images.

**Step 1: Research Content**

[Calls: web_search(
    query="sustainable living practices 2025 tips guide",
    mode="STANDARD"
)]

**Step 2: Generate Hero Image**

[Calls: image_generation(
    prompt="Bright, inspiring image of a modern sustainable home with solar panels, rooftop garden, rainwater collection system, and electric vehicle in driveway, blue sky background, photorealistic style",
    description="Sustainable Modern Home"
)]

**Step 3: Generate Supporting Images**

[Calls: image_generation(prompt="...")]

**Final Blog Post:**

# The Complete Guide to Sustainable Living in 2025

![Sustainable Modern Home](hero-image-url)

## Introduction
Sustainable living isn't just a trend—it's becoming essential for our planet's future...

## 1. Energy Efficiency
![Solar Panels](solar-image-url)
- Install solar panels
- Use LED lighting
- Upgrade to energy-efficient appliances

## 2. Water Conservation
![Rainwater Collection](water-image-url)
- Rainwater harvesting systems
- Low-flow fixtures
- Drought-resistant landscaping

[... rest of blog post ...]

## Conclusion
Small changes in daily habits can lead to significant environmental impact...
```

### Educational Content Creator

```
User: Teach me about photosynthesis with code simulations and diagrams

AI: I'll create an interactive educational experience about photosynthesis.

**Step 1: Research Latest Understanding**

[Calls: web_search(
    query="photosynthesis process detailed explanation recent research",
    mode="STANDARD"
)]

**Step 2: Create Diagram**

[Calls: image_generation(
    prompt="Clean educational diagram of photosynthesis showing chloroplast structure, light reactions in thylakoid, dark reactions in stroma, with arrows showing flow of H2O, CO2, O2, and glucose, labeled clearly, textbook illustration style",
    description="Photosynthesis Process Diagram"
)]

**Step 3: Create Interactive Simulation**

[Calls: code_interpreter(enable=True, use_jupyter=True)]

<code_interpreter type="code" lang="python">
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Simulate light intensity vs photosynthesis rate
light_intensity = np.linspace(0, 1000, 100)  # μmol/m²/s

def photosynthesis_rate(light, max_rate=100):
    """Michaelis-Menten kinetics for photosynthesis"""
    km = 200  # Half-saturation constant
    return (max_rate * light) / (km + light)

rate = photosynthesis_rate(light_intensity)

# Create visualization
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Rate vs Light Intensity
ax1.plot(light_intensity, rate, 'g-', linewidth=2)
ax1.fill_between(light_intensity, rate, alpha=0.3, color='green')
ax1.set_xlabel('Light Intensity (μmol/m²/s)')
ax1.set_ylabel('Photosynthesis Rate (μmol CO₂/m²/s)')
ax1.set_title('Light Response Curve')
ax1.grid(True, alpha=0.3)
ax1.axhline(y=50, color='r', linestyle='--', label='50% max rate')
ax1.legend()

# Plot 2: Inputs and Outputs
processes = ['Light\nEnergy', 'Water\n(H₂O)', 'Carbon\nDioxide\n(CO₂)',
             'Oxygen\n(O₂)', 'Glucose\n(C₆H₁₂O₆)']
values = [100, 6, 6, 6, 1]
colors = ['yellow', 'blue', 'gray', 'lightblue', 'orange']

bars = ax2.bar(range(len(processes)), values, color=colors, alpha=0.7)
ax2.set_xticks(range(len(processes)))
ax2.set_xticklabels(processes)
ax2.set_ylabel('Relative Molecules')
ax2.set_title('Photosynthesis: Inputs vs Outputs')

plt.tight_layout()
plt.savefig('photosynthesis_analysis.png', dpi=300)
print("✓ Simulation complete!")
print("\nKey Insights:")
print("- Light saturation occurs around 500 μmol/m²/s")
print("- Equation: 6CO₂ + 6H₂O + Light → C₆H₁₂O₆ + 6O₂")
print("- Efficiency: ~3-6% of light energy converted to chemical energy")
</code_interpreter>

# Understanding Photosynthesis

## The Process
![Photosynthesis Diagram](diagram-url)

## Light Response Curve
![Analysis](simulation-url)

## Key Concepts

**1. Light Reactions (Thylakoid)**
- Chlorophyll absorbs photons
- Water is split (photolysis)
- ATP and NADPH are produced

**2. Dark Reactions (Calvin Cycle)**
- CO₂ is fixed
- Glucose is synthesized
- Uses ATP and NADPH from light reactions

## Interactive Elements
The simulation above shows how photosynthesis rate changes with light intensity...
```

---

## Tips for Effective Tool Use

### 1. Choose the Right Search Mode

- **CRAWL**: When you have a specific URL
- **STANDARD**: For 90% of queries (news, facts, quick research)
- **COMPLETE**: Only for deep research needs
- **AUTO**: Let the system decide (safest default)

### 2. Code Interpreter Best Practices

- Always import all required libraries in the code block
- Save files to `/work` directory
- Use `uploader.upload_file()` to share results
- Print important outputs, don't rely on return values

### 3. Image Generation Tips

- Be specific and detailed in prompts
- Specify style (photorealistic, diagram, illustration, etc.)
- Include lighting, colors, composition details
- Provide context for better results

### 4. Combining Tools Effectively

- Research first, then analyze
- Generate images to illustrate findings
- Use code to validate web search data
- Create workflows: Research → Code → Visualize → Document

---

## Common Patterns

### Pattern 1: Research Paper
1. `web_search(mode="COMPLETE")` - Deep research
2. `code_interpreter()` - Analyze data
3. `image_generation()` - Create diagrams

### Pattern 2: Quick Answer
1. `web_search(mode="STANDARD")` - Get facts
2. Synthesize response

### Pattern 3: Data Story
1. `web_search(mode="STANDARD")` - Get context
2. `code_interpreter()` - Analyze data
3. `image_generation()` - Create visualization
4. Generate narrative

### Pattern 4: Educational Content
1. `web_search(mode="STANDARD")` - Research topic
2. `image_generation()` - Create diagrams
3. `code_interpreter()` - Interactive examples
4. Compile into lesson

---

**Happy building with the Agentic Master Tool!** 🚀
