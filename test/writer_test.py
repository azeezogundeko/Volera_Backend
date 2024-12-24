from agents import State, writer_agent_node, agent_manager
from schema import WSMessage
request = WSMessage(
    user_id="user_id",
    focus_mode=agent_manager.copilot_mode,
    files=["file1", "file2"],
    message={
        "content": "What is the cheapest laptop?"
    },
    history=[],
    optimization_mode="fast",
    
)
requirements = {
    "product_category": "laptop",
    "product_type": "",
    "purpose": "Python Programming",
    "preferred_brands": ["Lenovo", "hp"],
    "budget": "$1000"

}

results = {
  "results": [
    {
      "content": "# Product Information\n\n                ## Features\n                - **Name:** Hp CHROMEBOOK, INTEL CELERON, 4GB RAM,16GB EMMC + BAG\n                - **Description:** No description available\n                - **Brand:** Hp\n                - **Categories:**\n- Computing\n- Computers & Accessories\n- Computers & Tablets\n- Laptops\n                - **Key Features:**\n- Operating system: Chrome\n- Processor: Intel Celeron N2846\n- Display: 11.0-inch diagonal, HD (1366 x 768), micro-edge, BrightView\n- Memory: 4 GB LPDDR3-2400 SDRAM (onboard)\n- Internal storage: 16 GB eMMC\n- Graphics: Intel UHD Graphics 600\n- Battery life: Up to 12 hours and 30 minutes (mixed usage)\n- Wireless: Realtek RTL8822CE 802.11a/b/g/n/ac (2x2) Wi-Fi and Bluetooth 5.0 combo\n- Camera: HP Wide Vision 720p HD camera with integrated dual array digital microphones\n                - **Box Contents:**\n\n\n                ## Pricing and Discounts\n                - **Current Price:** ₦ 120,000\n                - **Old Price:** ₦ 140,000\n                - **Discount:** 14%\n                ",
      "metadata": {
        "title": "Hp CHROMEBOOK, INTEL CELERON, 4GB RAM,16GB EMMC + BAG",
        "price": 120,
        "discount": 0.14,
        "image_url": "https://ng.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/98/3462691/1.jpg?1813",
        "product_url": "https://www.jumia.com.ng//chromebook-intel-celeron-4gb-ram16gb-emmc-bag-hp-mpg3588057.html"
      }
    },
    {
      "content": "# Product Information\n\n                ## Features\n                - **Name:** Hp CHROMEBOOK11, CELERON, 4GB RAM,16GB SSD + 32GBFLASH\n                - **Description:** No description available\n                - **Brand:** Hp\n                - **Categories:**\n- Computing\n- Computers & Accessories\n- Computers & Tablets\n- Laptops\n                - **Key Features:**\n- Operating system: Chrome\n- Processor: Intel Celeron N2846\n- Display: 11.0-inch diagonal, HD (1366 x 768), micro-edge, BrightView\n- Memory: 4 GB LPDDR3-2400 SDRAM (onboard)\n- Internal storage: 16 GB eMMC\n- Graphics: Intel UHD Graphics 600\n- Battery life: Up to 12 hours and 30 minutes (mixed usage)\n- Wireless: Realtek RTL8822CE 802.11a/b/g/n/ac (2x2) Wi-Fi and Bluetooth 5.0 combo\n- Camera: HP Wide Vision 720p HD camera with integrated dual array digital microphones\n                - **Box Contents:**\n\n\n                ## Pricing and Discounts\n                - **Current Price:** ₦ 120,000\n                - **Old Price:** ₦ 240,000\n                - **Discount:** 50%\n                ",
      "metadata": {
        "title": "Hp CHROMEBOOK11, CELERON, 4GB RAM,16GB SSD + 32GBFLASH",
        "price": 120,
        "discount": 0.5,
        "image_url": "https://ng.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/10/1295051/1.jpg?8729",
        "product_url": "https://www.jumia.com.ng//chromebook11-celeron-4gb-ram16gb-ssd-32gbflash-hp-mpg8253521.html"
      }
    },
    {
      "content": "# Product Information\n\n                ## Features\n                - **Name:** Hp CHROMEBOOK 11 G4, CELERON, 4GB RAM,16GB SSD + BAG\n                - **Description:** No description available\n                - **Brand:** Hp\n                - **Categories:**\n- Computing\n- Computers & Accessories\n- Computers & Tablets\n- Laptops\n                - **Key Features:**\n- Operating system: Chrome\n- Processor: Intel Celeron N2846\n- Display: 11.0-inch diagonal, HD (1366 x 768), micro-edge, BrightView\n- Memory: 4 GB LPDDR3-2400 SDRAM (onboard)\n- Internal storage: 16 GB eMMC\n- Graphics: Intel UHD Graphics 600\n- Battery life: Up to 12 hours and 30 minutes (mixed usage)\n- Wireless: Realtek RTL8822CE 802.11a/b/g/n/ac (2x2) Wi-Fi and Bluetooth 5.0 combo\n- Camera: HP Wide Vision 720p HD camera with integrated dual array digital microphones\n                - **Box Contents:**\n\n\n                ## Pricing and Discounts\n                - **Current Price:** ₦ 120,000\n                - **Old Price:** ₦ 220,000\n                - **Discount:** 45%\n                ",
      "metadata": {
        "title": "Hp CHROMEBOOK 11 G4, CELERON, 4GB RAM,16GB SSD + BAG",
        "price": 120,
        "discount": 0.45,
        "image_url": "https://ng.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/76/8795051/1.jpg?4488",
        "product_url": "https://www.jumia.com.ng//chromebook11-celeron-4gb-ram16gb-ssd-bag-hp-mpg3588053.html"
      }
    },
    {
      "content": "# Product Information\n\n                ## Features\n                - **Name:** Hp Stream 11 Laptop- Intel Celeron - 64GB SSD 4GB RAM Windows 10 PRO+ Mouse & USB Light For Keyboard\n                - **Description:** No description available\n                - **Brand:** Hp\n                - **Categories:**\n- Computing\n- Computers & Accessories\n- Computers & Tablets\n- Laptops\n                - **Key Features:**\n- STREAM 11 NOTEBOOK\n- INTEL CELERON FAST PROCESSOR\n- 64GB STORAGE SPACE\n- 4GB RAM\n- 1TB OF OneDrive Cloud Storage\n- Thinner, Lighter Design\n- Fast, Durable And Mobile\n                - **Box Contents:**\n\n\n                ## Pricing and Discounts\n                - **Current Price:** 190000.0\n                - **Old Price:** ₦ 300,000\n                - **Discount:** 37%\n                ",
      "metadata": {
        "title": "Hp Stream 11 Laptop- Intel Celeron - 64GB SSD 4GB RAM Windows 10 PRO+ Mouse & USB Light For Keyboard",
        "price": 190,
        "discount": 0.37,
        "image_url": "https://ng.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/56/2828913/1.jpg?6186",
        "product_url": "https://www.jumia.com.ng//hp-stream-11-laptop-intel-celeron-64gb-ssd-4gb-ram-windows-10-pro-mouse-usb-light-for-keyboard-319828265.html"
      }
    },
    {
      "content": "# Product Information\n\n                ## Features\n                - **Name:** Hp Stream 11 Laptop- Intel Celeron - 64GB SSD 4GB RAM Windows 10 PRO+ Mouse & USB Light For Keyboard\n                - **Description:** No description available\n                - **Brand:** Hp\n                - **Categories:**\n- Computing\n- Computers & Accessories\n- Computers & Tablets\n- Laptops\n                - **Key Features:**\n- STREAM 11 NOTEBOOK\n- INTEL CELERON FAST PROCESSOR\n- 64GB STORAGE SPACE\n- 4GB RAM\n- 1TB OF OneDrive Cloud Storage\n- Thinner, Lighter Design\n- Fast, Durable And Mobile\n                - **Box Contents:**\n\n\n                ## Pricing and Discounts\n                - **Current Price:** ₦ 190,000\n                - **Old Price:** ₦ 300,000\n                - **Discount:** 37%\n                ",
      "metadata": {
        "title": "Hp Stream 11 Laptop- Intel Celeron - 64GB SSD 4GB RAM Windows 10 PRO+ Mouse & USB Light For Keyboard",
        "price": 190,
        "discount": 0.37,
        "image_url": "https://ng.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/56/2828913/1.jpg?6186",
        "product_url": "https://www.jumia.com.ng//hp-stream-11-laptop-intel-celeron-64gb-ssd-4gb-ram-windows-10-pro-mouse-usb-light-for-keyboard-319828265.html"
      }
    },
    {
      "content": "# Product Information\n\n                ## Features\n                - **Name:** Hp Stream 11 Laptop- Intel Celeron - 64GB SSD 4GB RAM Windows 10 PRO+ Mouse & USB Light For Keyboard\n                - **Description:** No description available\n                - **Brand:** Hp\n                - **Categories:**\n- Computing\n- Computers & Accessories\n- Computers & Tablets\n- Laptops\n                - **Key Features:**\n- STREAM 11 NOTEBOOK\n- INTEL CELERON FAST PROCESSOR\n- 64GB STORAGE SPACE\n- 4GB RAM\n- 1TB OF OneDrive Cloud Storage\n- Thinner, Lighter Design\n- Fast, Durable And Mobile\n                - **Box Contents:**\n\n\n                ## Pricing and Discounts\n                - **Current Price:** ₦ 190,000\n                - **Old Price:** ₦ 300,000\n                - **Discount:** 37%\n                ",
      "metadata": {
        "title": "Hp Stream 11 Laptop- Intel Celeron - 64GB SSD 4GB RAM Windows 10 PRO+ Mouse & USB Light For Keyboard",
        "price": 190,
        "discount": 0.37,
        "image_url": "https://ng.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/56/2828913/1.jpg?6186",
        "product_url": "https://www.jumia.com.ng//hp-stream-11-laptop-intel-celeron-64gb-ssd-4gb-ram-windows-10-pro-mouse-usb-light-for-keyboard-319828265.html"
      }
    },
    {
      "content": "# Product Information\n\n                ## Features\n                - **Name:** Hp Stream 11 Laptop- Intel Celeron - 64GB SSD 4GB RAM Windows 10 PRO+ Mouse & USB Light For Keyboard\n                - **Description:** No description available\n                - **Brand:** Hp\n                - **Categories:**\n- Computing\n- Computers & Accessories\n- Computers & Tablets\n- Laptops\n                - **Key Features:**\n- STREAM 11 NOTEBOOK\n- INTEL CELERON FAST PROCESSOR\n- 64GB STORAGE SPACE\n- 4GB RAM\n- 1TB OF OneDrive Cloud Storage\n- Thinner, Lighter Design\n- Fast, Durable And Mobile\n                - **Box Contents:**\n\n\n                ## Pricing and Discounts\n                - **Current Price:** ₦ 190,000\n                - **Old Price:** ₦ 300,000\n                - **Discount:** 37%\n                ",
      "metadata": {
        "title": "Hp Stream 11 Laptop- Intel Celeron - 64GB SSD 4GB RAM Windows 10 PRO+ Mouse & USB Light For Keyboard",
        "price": 190,
        "discount": 0.37,
        "image_url": "https://ng.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/56/2828913/1.jpg?6186",
        "product_url": "https://www.jumia.com.ng//hp-stream-11-laptop-intel-celeron-64gb-ssd-4gb-ram-windows-10-pro-mouse-usb-light-for-keyboard-319828265.html"
      }
    },
    {
      "content": "# Product Information\n\n                ## Features\n                - **Name:** Hp STREAM 11 LAPTOP- CELERON-64GB 4D 4GB RAM Windows 10 PRO+ & USB Light For Keyboard\n                - **Description:** No description available\n                - **Brand:** Hp\n                - **Categories:**\n- Computing\n- Computers & Accessories\n- Computers & Tablets\n- Laptops\n- Traditional Laptops\n- Notebooks\n                - **Key Features:**\n- STREAM 11 INCH LAPTOP\n- FAST INTEL CELERON PROCESSOR\n- 64GB STORAGE DRIVE SPACE\n- 4GB RAM\n- FAST AND MOBILE\n                - **Box Contents:**\n\n\n                ## Pricing and Discounts\n                - **Current Price:** ₦ 160,000\n                - **Old Price:** ₦ 250,000\n                - **Discount:** 36%\n                ",
      "metadata": {
        "title": "Hp STREAM 11 LAPTOP- CELERON-64GB 4D 4GB RAM Windows 10 PRO+ & USB Light For Keyboard",
        "price": 160,
        "discount": 0.36,
        "image_url": "https://ng.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/34/3716553/1.jpg?6645",
        "product_url": "https://www.jumia.com.ng//hp-stream-11-laptop-celeron-64gb-4d-4gb-ram-windows-10-pro-usb-light-for-keyboard-355617343.html"
      }
    },
    {
      "content": "# Product Information\n\n                ## Features\n                - **Name:** Hp Notebook 11 Pro G5 TOUCHSCREEN-128GB SSD 4GB RAM- Intel Celeron - Windows 10 Pro + Bag\n                - **Description:** No description available\n                - **Brand:** Hp\n                - **Categories:**\n- Computing\n- Computers & Accessories\n- Computers & Tablets\n- Laptops\n- Traditional Laptops\n- Netbooks\n                - **Key Features:**\n- SKU: LE842CL134KKTNAFAMZ\n- Product Line: Arklandtech Integrated System Ltd\n- Model: Notebook 11\n- Weight (kg): 1.1\n- Color: grey\n                - **Box Contents:**\n\n\n                ## Pricing and Discounts\n                - **Current Price:** ₦ 220,000\n                - **Old Price:** ₦ 690,000\n                - **Discount:** 68%\n                ",
      "metadata": {
        "title": "Hp Notebook 11 Pro G5 TOUCHSCREEN-128GB SSD 4GB RAM- Intel Celeron - Windows 10 Pro + Bag",
        "price": 220,
        "discount": 0.68,
        "image_url": "https://ng.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/65/718317/1.jpg?4872",
        "product_url": "https://www.jumia.com.ng//notebook-11-pro-g5-touchscreen-128gb-ssd-4gb-ram-intel-celeron-windows-10-pro-bag-hp-mpg7126952.html"
      }
    },
    {
      "content": "# Product Information\n\n                ## Features\n                - **Name:** Hp CHROMEBOOK  INTEL CELERON ,4GB RAM,16GB WINDOWS 10\n                - **Description:** No description available\n                - **Brand:** Hp\n                - **Categories:**\n- Computing\n- Computers & Accessories\n- Computers & Tablets\n- Laptops\n                - **Key Features:**\n- Aspect Ratio: 16:9\n- Product Type: Chromebook\n- Number of Cells: 2-cell\n- Screen Resolution: 1366 x 768\n- Standard Memory: 4 GB\n- Weight (Approximate): 1.14 kg\n- Operating System: Chrome OS\n- Processor Speed: 1.60 GHz\n- Processor Type: Celeron\n- Screen Size: 11.6\"\n                - **Box Contents:**\n\n\n                ## Pricing and Discounts\n                - **Current Price:** ₦ 120,000\n                - **Old Price:** ₦ 228,000\n                - **Discount:** 47%\n                ",
      "metadata": {
        "title": "Hp CHROMEBOOK  INTEL CELERON ,4GB RAM,16GB WINDOWS 10",
        "price": 120,
        "discount": 0.47,
        "image_url": "https://ng.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/25/8075051/1.jpg?8809",
        "product_url": "https://www.jumia.com.ng//hp-chromebook-intel-celeron-4gb-ram16gb-windows-10-150570852.html"
      }
    }
  ],
  "total_results": 10,
  "search_query": "laptop Lenovo HP",
  "processing_time": None
}


instructions = ['Summarize the specifications of the laptops.', 'Present the price of the laptops.']
state = State(
    ws_message=request,
    final_result={},
    chat_limit=10,
    chat_finished=False,
    previous_node="",
    previous_search_queries=[],
    message_history=[],
    agent_results={
        "search_tool": results,
        agent_manager.planner_agent: {
            "writer_instructions": instructions
        }
    },
    requirements=requirements
)

async def test_writer_agent_node(state):
    result = await writer_agent_node(state)
    print(result)

if __name__ == "__main__":
    import asyncio

    asyncio.run(test_writer_agent_node(state))