import { TripData } from "../types/trip";

export const mockKeralaTrip: TripData = {
  trip_id: "trip-kerala-2027",
  title: "7-Day Kerala Discovery: Kochi, Munnar & Alleppey",
  destination_summary: "Kochi, Munnar, Alleppey, Kerala",
  destinations: ["Kochi", "Munnar", "Alleppey"],
  travel_dates: {
    start: "10 Jan 2027",
    end: "17 Jan 2027",
    duration_days: 7,
    formatted: "10 Jan 2027 – 17 Jan 2027 (7 Nights)",
  },
  travelers: {
    count: 3,
    label: "3 Adults",
  },
  status: "Verified Plan",
  overview:
    "A meticulously paced 7-day journey through the finest landscapes of Kerala. From the colonial lanes and Portuguese architecture of Fort Kochi, ascend through Western Ghats tea plantations and cool mist in Munnar, before unwinding on the Venetian backwaters and lagoons of Alleppey. All flight schedules, boutique stays with HasData live rates, and scenic private transfers have been verified for 3 adults within the ₹90,000 budget.",
  itinerary: [
    {
      day: 1,
      date: "10 Jan 2027",
      destination: "Kochi",
      title: "Arrival in Kochi & Fort Kochi Colonial Heritage",
      summary: "Arrive at Cochin International Airport (COK). Transfer to hotel in Fort Kochi and explore heritage landmarks.",
      activities: [
        {
          time: "Morning",
          title: "DEL → COK Flight Arrival & Transfer",
          description: "Arrive via morning flight at Cochin International Airport. Private AC sedan transfer to your boutique heritage hotel in Fort Kochi (approx. 42 km, 75 mins).",
          tag: "Transit & Check-in",
        },
        {
          time: "Afternoon",
          title: "Chinese Fishing Nets & St. Francis Church",
          description: "Walk along Vasco da Gama Square to witness the 14th-century cantilevered Chinese fishing nets. Visit St. Francis Church, India's oldest European church where Vasco da Gama was initially buried.",
          tag: "Heritage Walk",
        },
        {
          time: "Evening",
          title: "Kathakali Classical Dance Performance",
          description: "Experience an authentic Kathakali performance at Kerala Kathakali Centre, including an up-close facial makeup demonstration illustrating the nine classical rasas.",
          tag: "Cultural Arts",
        },
      ],
      transit: {
        from: "Delhi (DEL)",
        to: "Kochi (COK)",
        mode: "Direct Flight",
        duration: "3h 15m",
      },
    },
    {
      day: 2,
      date: "11 Jan 2027",
      destination: "Kochi",
      title: "Mattancherry Palaces, Jew Town & Harbour Sunset",
      summary: "Delve into Cochin's spice trading history, Jewish synagogue, and twilight harbour sailing.",
      activities: [
        {
          time: "Morning",
          title: "Mattancherry Palace (Dutch Palace)",
          description: "Explore the 1555 Portuguese palace gifted to the Raja of Kochi, celebrated for intricate Ramayana and Mahabharata tempera wall murals and royal coronation robes.",
          tag: "Architecture",
        },
        {
          time: "Afternoon",
          title: "Paradesi Synagogue & Antique Jew Town",
          description: "Walk through Jew Town's cobbled alleys, visit the 1568 Paradesi Synagogue with Belgian crystal chandeliers and hand-painted Chinese porcelain tiles, and browse artisan spice warehouses.",
          tag: "Shopping & Spice",
        },
        {
          time: "Evening",
          title: "Sunset Cruise on Cochin Harbour",
          description: "Take a scenic twilight catamaran cruise from Marine Drive, catching golden hour over the Arabian Sea, Bolgatty Palace, and bustling shipping channels.",
          tag: "Scenic Waterways",
        },
      ],
      transit: null,
    },
    {
      day: 3,
      date: "12 Jan 2027",
      destination: "Munnar",
      title: "Scenic Western Ghats Ascent to Munnar Tea Country",
      summary: "Scenic mountain drive via NH 85 with stops at cascading waterfalls before entering Munnar's rolling tea estates.",
      activities: [
        {
          time: "Morning",
          title: "Scenic Mountain Drive & Cheeyappara Falls",
          description: "Depart Fort Kochi in a private AC cab ascending the Western Ghats along NH 85. Stop at Cheeyappara and Valara waterfalls for photos and fresh cardamom tea.",
          tag: "Mountain Transit",
        },
        {
          time: "Afternoon",
          title: "Resort Check-in & KDHP Tea Museum",
          description: "Check into your hill resort with valley views. Visit the Tata Tea Museum in Nallathanni Estate to witness orthodox and CTC tea processing and historical machinery.",
          tag: "Tea Heritage",
        },
        {
          time: "Evening",
          title: "Munnar Town Walk & Homemade Chocolates",
          description: "Stroll Munnar town market, sampling locally made spice-infused chocolates, pure eucalyptus oil, and freshly plucked high-altitude green tea.",
          tag: "Leisure",
        },
      ],
      transit: {
        from: "Kochi",
        to: "Munnar",
        mode: "Private AC Sedan",
        distance: "125 km",
        duration: "3h 45m",
      },
    },
    {
      day: 4,
      date: "13 Jan 2027",
      destination: "Munnar",
      title: "Eravikulam National Park Safari & High Altitude Lakes",
      summary: "Spot the endangered Nilgiri Tahr mountain goat and cruise tranquil mountain reservoirs.",
      activities: [
        {
          time: "Morning",
          title: "Eravikulam National Park (Rajamalai)",
          description: "Early morning eco-safari through rolling Shola grasslands beneath Anamudi peak (2,695 m, highest in South India) to observe the endangered Nilgiri Tahr in their natural habitat.",
          tag: "Wildlife Safari",
        },
        {
          time: "Afternoon",
          title: "Mattupetty Dam & Echo Point",
          description: "Visit Mattupetty concrete gravity dam, enjoy a speedboat ride on the reservoir, and test natural vocal resonance at the lush Echo Point basin.",
          tag: "Nature & Lake",
        },
        {
          time: "Evening",
          title: "Kundala Lake & Tea Plantation Sunset",
          description: "Pedal boat ride at Kundala arch dam surrounded by pine and cherry blossom woods, returning through misty tea estate viewpoints as mist rolls over valleys.",
          tag: "Golden Hour",
        },
      ],
      transit: null,
    },
    {
      day: 5,
      date: "14 Jan 2027",
      destination: "Alleppey",
      title: "Descent from Hills to Venetian Backwaters",
      summary: "Descend from the misty mountains to the palm-lined canals and Vembanad Lake basin.",
      activities: [
        {
          time: "Morning",
          title: "Descent to Alappuzha Canals",
          description: "Depart Munnar through tea terraces and rubber groves toward the coastal lowlands of Alappuzha (Alleppey), arriving in time for waterfront check-in.",
          tag: "Scenic Transit",
        },
        {
          time: "Afternoon",
          title: "Waterfront Check-in & Coir Village Walk",
          description: "Check into your tranquil backwater property along the canal. Stroll through neighbouring village hamlets witnessing traditional coir rope weaving and canoe fishing.",
          tag: "Village Experience",
        },
        {
          time: "Evening",
          title: "Alappuzha Beach & Old Sea Pier",
          description: "Catch the sunset at Alappuzha Beach, walking along the remnants of the 150-year-old historic iron sea bridge and the vintage red-and-white coastal lighthouse.",
          tag: "Coastal Leisure",
        },
      ],
      transit: {
        from: "Munnar",
        to: "Alleppey",
        mode: "Private AC Sedan",
        distance: "172 km",
        duration: "4h 30m",
      },
    },
    {
      day: 6,
      date: "15 Jan 2027",
      destination: "Alleppey",
      title: "Traditional Houseboat Cruise & Kuttanad Waterways",
      summary: "Full day private cruise exploring below-sea-level paddy farming and tranquil lagoons.",
      activities: [
        {
          time: "Morning",
          title: "Private Kettuvallam Cruise Embarkation",
          description: "Board a traditional thatched-roof wooden houseboat (kettuvallam) at Punnamada Jetty, gliding across expansive Vembanad Lake, India's longest lake.",
          tag: "Backwater Cruise",
        },
        {
          time: "Afternoon",
          title: "Traditional Kerala Sadya Feast on Water",
          description: "Savour an authentic onboard luncheon prepared by the resident chef: fresh Karimeen Pollichathu (pearl spot fish wrapped in banana leaf), red Kuttanad rice, avial, and payasam.",
          tag: "Authentic Dining",
        },
        {
          time: "Evening",
          title: "Narrow Canal Shikara Exploration",
          description: "Switch to an intimate covered wooden shikara canoe to gently glide through shallow, narrow village canals where large boats cannot navigate.",
          tag: "Hidden Waterways",
        },
      ],
      transit: null,
    },
    {
      day: 7,
      date: "16 Jan 2027",
      destination: "Alleppey / Kochi",
      title: "Rest Day & Return Departure to Delhi (DEL)",
      summary: "Dedicated rest and recovery day. Zero sightseeing scheduled so you can rest comfortably at the resort, sleep in, pack at leisure, and travel home refreshed.",
      activities: [
        {
          time: "Morning",
          title: "Rest & Leisurely Resort Breakfast",
          description: "Sleep in with no alarm, enjoy a peaceful breakfast overlooking the backwaters. Zero sightseeing activities planned to ensure complete rest and recovery.",
          tag: "Rest & Recovery",
        },
        {
          time: "Afternoon",
          title: "Relaxation, Packing & Resort Check-out",
          description: "Take time packing comfortably, enjoy the resort lounge and tranquil amenities, and check out without any rush or stress.",
          tag: "Relaxation & Leisure",
        },
        {
          time: "Evening",
          title: "Cochin Airport (COK) Departure to DEL",
          description: "Transfer to Cochin International Airport (COK) Terminal 1 for your evening non-stop return flight back to Indira Gandhi International Airport (DEL).",
          tag: "Return Flight",
        },
      ],
      transit: {
        from: "Alleppey",
        to: "Cochin Airport (COK)",
        mode: "Private AC Sedan",
        distance: "75 km",
        duration: "2h 10m",
      },
    },
  ],
  flights: [
    {
      id: "fl-outbound",
      airline: "IndiGo",
      flight_number: "6E-2015",
      origin: "DEL",
      destination: "COK",
      departure_date: "10 Jan 2027",
      departure_time: "06:15",
      arrival_date: "10 Jan 2027",
      arrival_time: "09:30",
      duration: "3h 15m",
      stops: 0,
      price: 5250,
      currency: "INR",
      baggage: "15 kg Check-in + 7 kg Cabin per passenger",
      booking_url: "https://www.goindigo.in",
      is_round_trip: true,
      verified_status: "Verified GDS Search Result",
      outbound_journey: {
        route: "DEL -> COK",
        departure: "10 Jan 2027 06:15 (Indira Gandhi T2)",
        arrival: "10 Jan 2027 09:30 (Cochin T1)",
        flight_number: "6E-2015",
        stops: 0,
        airline: "IndiGo",
      },
      return_journey: {
        route: "COK -> DEL",
        departure: "17 Jan 2027 19:40 (Cochin T1)",
        arrival: "17 Jan 2027 22:55 (Indira Gandhi T2)",
        flight_number: "6E-2184",
        stops: 0,
        airline: "IndiGo",
      },
    },
    {
      id: "fl-alt-1",
      airline: "Air India",
      flight_number: "AI-512",
      origin: "DEL",
      destination: "COK",
      departure_date: "10 Jan 2027",
      departure_time: "09:10",
      arrival_date: "10 Jan 2027",
      arrival_time: "12:35",
      duration: "3h 25m",
      stops: 0,
      price: 5890,
      currency: "INR",
      baggage: "20 kg Check-in + 7 kg Cabin per passenger",
      booking_url: "https://www.airindia.com",
      is_round_trip: true,
      verified_status: "Verified GDS Search Result",
      outbound_journey: {
        route: "DEL -> COK",
        departure: "10 Jan 2027 09:10",
        arrival: "10 Jan 2027 12:35",
        flight_number: "AI-512",
        stops: 0,
        airline: "Air India",
      },
    },
    {
      id: "fl-alt-2",
      airline: "Akasa Air",
      flight_number: "QP-1402",
      origin: "DEL",
      destination: "COK",
      departure_date: "10 Jan 2027",
      departure_time: "14:20",
      arrival_date: "10 Jan 2027",
      arrival_time: "17:35",
      duration: "3h 15m",
      stops: 0,
      price: 4950,
      currency: "INR",
      baggage: "15 kg Check-in + 7 kg Cabin per passenger",
      booking_url: "https://www.akasaair.com",
      is_round_trip: true,
      verified_status: "Verified GDS Search Result",
    },
  ],
  hotels: [
    {
      id: "ht-kochi",
      property_name: "Forte Kochi Heritage Boutique Hotel",
      destination_city: "Kochi",
      address: "1/290, Princess Street, Fort Kochi, Kochi 682001, India",
      hotel_class: 4,
      rating: 4.7,
      reviews: 1420,
      price_per_night: 4200,
      total_price: 8400,
      currency: "INR",
      live_rates_available: true,
      pricing_notice: "Verified live rate via HasData Google Hotels (2 nights, 3 adults).",
      recommended_rooms: "1 Heritage Triple Room with extra bed (or 2 Deluxe Rooms)",
      room_guidance: "Accommodates 3 adults comfortably with complimentary breakfast and courtyard pool.",
      check_in_date: "10 Jan 2027",
      check_out_date: "12 Jan 2027",
      nights: 2,
      booking_url: "https://www.google.com/travel/hotels",
      image_url: "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80",
      amenities: ["Swimming Pool", "Heritage Courtyard", "Free High-Speed Wi-Fi", "Complimentary Breakfast", "Airport Shuttle"],
    },
    {
      id: "ht-munnar",
      property_name: "Amber Dale Luxury Mountain Resort & Spa",
      destination_city: "Munnar",
      address: "Pallivasal, Munnar 685565, Kerala, India",
      hotel_class: 4,
      rating: 4.6,
      reviews: 2180,
      price_per_night: 4600,
      total_price: 9200,
      currency: "INR",
      live_rates_available: true,
      pricing_notice: "Verified live rate via HasData Google Hotels (2 nights, 3 adults).",
      recommended_rooms: "1 Premium Valley View Room with rollaway bed",
      room_guidance: "Panoramic valley mist views, complimentary morning guided tea plantation walk.",
      check_in_date: "12 Jan 2027",
      check_out_date: "14 Jan 2027",
      nights: 2,
      booking_url: "https://www.google.com/travel/hotels",
      image_url: "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=800&q=80",
      amenities: ["Valley View Balcony", "Ayurvedic Spa", "Game Room", "Multi-Cuisine Dining", "Tea Tasting Sessions"],
    },
    {
      id: "ht-alleppey",
      property_name: "Lake Palace Backwater Resort & Private Villas",
      destination_city: "Alleppey",
      address: "Thirumala Ward, Chungam, Alappuzha 688011, Kerala, India",
      hotel_class: 4,
      rating: 4.8,
      reviews: 980,
      price_per_night: 4700,
      total_price: 14100,
      currency: "INR",
      live_rates_available: true,
      pricing_notice: "Verified live rate via HasData Google Hotels (3 nights, 3 adults).",
      recommended_rooms: "1 Lakefront Cottage with extra single bed",
      room_guidance: "Direct Vembanad lake frontage, private pedal boats, evening cultural shows included.",
      check_in_date: "14 Jan 2027",
      check_out_date: "17 Jan 2027",
      nights: 3,
      booking_url: "https://www.google.com/travel/hotels",
      image_url: "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80",
      amenities: ["Direct Lake Access", "Ayurvedic Center", "Sunset Shikara Cruise", "Infinity Pool", "Waterfront Restaurant"],
    },
  ],
  routes: [
    {
      origin: "Kochi",
      destination: "Munnar",
      distance_km: 125,
      duration_text: "3 hours 45 mins",
      highway: "NH 85 (Kochi-Dhanushkodi Road)",
      key_stops: ["Kothamangalam", "Cheeyappara Waterfalls", "Valara Waterfalls", "Adimali"],
    },
    {
      origin: "Munnar",
      destination: "Alleppey",
      distance_km: 172,
      duration_text: "4 hours 30 mins",
      highway: "SH 43 / NH 183 via Pala & Changanassery",
      key_stops: ["Kothamangalam", "Muvattupuzha", "Kottayam", "Vembanad Lowlands"],
    },
    {
      origin: "Alleppey",
      destination: "Cochin Airport (COK)",
      distance_km: 75,
      duration_text: "2 hours 10 mins",
      highway: "NH 66 / Salem-Kanyakumari Highway",
      key_stops: ["Cherthala", "Aroor Bridge", "Edappally Bypass"],
    },
  ],
  weather: [
    {
      city: "Kochi",
      region: "Kerala",
      temperature_c: 28,
      condition: "Partly Cloudy",
      humidity: 72,
      feels_like_c: 30,
      observation_timestamp: "Real-time observation via WeatherAPI",
      classification: "Pleasant coastal warmth. Ideal for evening heritage walking and boat rides.",
    },
    {
      city: "Munnar",
      region: "Kerala Western Ghats",
      temperature_c: 16,
      condition: "Crisp & Misty",
      humidity: 64,
      feels_like_c: 15,
      observation_timestamp: "Real-time observation via WeatherAPI",
      classification: "Cool hill station climate (night temps 10–12°C). Light woollens/jackets recommended.",
    },
    {
      city: "Alleppey",
      region: "Kerala Backwaters",
      temperature_c: 27,
      condition: "Sunny & Breezy",
      humidity: 68,
      feels_like_c: 29,
      observation_timestamp: "Real-time observation via WeatherAPI",
      classification: "Mild tropical breezes over backwaters. Light cotton clothing recommended.",
    },
  ],
  attractions: [
    {
      name: "Fort Kochi & Chinese Fishing Nets",
      rating: 4.8,
      categories: ["Heritage", "Scenic", "Sights"],
      description: "Iconic shorelines featuring 14th-century cantilevered fishing nets and colonial Portuguese streets.",
      address: "Fort Kochi Beach Walkway, Kochi, Kerala",
      city: "Kochi",
      provider: "Apify MCP Server (happitap/city-tourism-attractions-finder)",
    },
    {
      name: "Mattancherry Palace (Dutch Palace)",
      rating: 4.6,
      categories: ["Museum", "History", "Royal"],
      description: "Portuguese-built palace showcasing magnificent mythological murals and royal artifacts.",
      address: "Mattancherry, Kochi, Kerala",
      city: "Kochi",
      provider: "Apify MCP Server (happitap/city-tourism-attractions-finder)",
    },
    {
      name: "Eravikulam National Park",
      rating: 4.7,
      categories: ["Nature", "Wildlife", "Trek"],
      description: "Home of the endangered Nilgiri Tahr with rolling misty hills and blooming Neelakurinji flowers.",
      address: "Kannandevan Hills, Munnar, Kerala",
      city: "Munnar",
      provider: "Apify MCP Server (happitap/city-tourism-attractions-finder)",
    },
    {
      name: "KDHP Tea Museum & Factory",
      rating: 4.5,
      categories: ["Museum", "Culture", "Tea Estate"],
      description: "Fascinating demonstration of orthodox tea processing nestled amidst century-old plantations.",
      address: "Nullatanni Estate, Munnar, Kerala",
      city: "Munnar",
      provider: "Apify MCP Server (happitap/city-tourism-attractions-finder)",
    },
    {
      name: "Alleppey Backwaters & Punnamada Lake",
      rating: 4.9,
      categories: ["Backwaters", "Scenic", "Boat Cruise"],
      description: "Serene palm-fringed waterways, traditional wooden houseboats, and tranquil village waterways.",
      address: "Vembanad Lake Basin, Alleppey, Kerala",
      city: "Alleppey",
      provider: "Apify MCP Server (happitap/city-tourism-attractions-finder)",
    },
    {
      name: "Marari Beach",
      rating: 4.6,
      categories: ["Beaches", "Relaxation", "Sunset"],
      description: "Pristine white sand coastal stretch surrounded by coconut palms and quiet fishing hamlets.",
      address: "Mararikulam, Alleppey, Kerala",
      city: "Alleppey",
      provider: "Apify MCP Server (happitap/city-tourism-attractions-finder)",
    },
  ],
  budget: {
    user_budget: 90000,
    estimated_total: 88700,
    currency: "INR",
    currency_symbol: "₹",
    difference: 1300,
    is_within_budget: true,
    status_label: "Within Budget",
    status_color: "emerald",
    categories: [
      {
        name: "Flights (Round-Trip DEL ⇄ COK for 3)",
        amount: 31500,
        percentage: 35.5,
        color: "#1B4332",
      },
      {
        name: "Hotels & Stays (7 Nights for 3 Adults)",
        amount: 31700,
        percentage: 35.7,
        color: "#2D6A4F",
      },
      {
        name: "Transportation (7 Days AC Cab & Fuel)",
        amount: 11500,
        percentage: 13.0,
        color: "#40916C",
      },
      {
        name: "Food & Dining (7 Days for 3 Adults)",
        amount: 8500,
        percentage: 9.6,
        color: "#52B788",
      },
      {
        name: "Sightseeing, Safaris & Shikara Cruise",
        amount: 3500,
        percentage: 3.9,
        color: "#74C69D",
      },
      {
        name: "Contingency & Miscellaneous Buffer",
        amount: 2000,
        percentage: 2.3,
        color: "#B7E4C7",
      },
    ],
  },
  final_response: `### Trip Overview

A seven-day Kerala experience for three adults, travelling from Delhi (DEL) to Kochi, Munnar and Alleppey between 10 and 17 January 2027. The itinerary blends colonial heritage in Fort Kochi, Western Ghats tea plantations in Munnar, and authentic backwater houseboat cruising in Alleppey within a total budget of ₹90,000.

### Flight Details

| Leg | Airline and Flight | Date and Time | Route | Duration | Price (INR) | Booking Link |
|:---|:---|:---|:---|:---|:---|:---|
| **Outbound** | IndiGo (6E) – 6E6262 | 10 Jan 2027, 17:55 – 21:05 | Delhi (DEL) → Kochi (COK) | 3h 10m | ₹23,294.16 | Direct Flight |
| **Return** | IndiGo (6E) – 6E2127 | 17 Jan 2027, 21:40 – 00:50 (18 Jan) | Kochi (COK) → Delhi (DEL) | 3h 10m | ₹23,294.16 | Direct Flight |
| **Total** | – | – | – | – | **₹46,588.32** | – |

*Note: Fare includes the full party of 3 adults with 7 kg cabin baggage.*

### Accommodation Options (HasData Google Hotels Live Rates)

| Destination | Property Name | Star Class | Guest Rating | Nightly Rate | Total Stay Rate | Booking Channel |
|:---|:---|:---|:---|:---|:---|:---|
| **Kochi** | Hotel Abad Fort | 3-star | 4.1 ⭐ | ₹5,300 | ₹10,601 | Verify directly |
| **Munnar** | Birdwing Cottage | 4-star | 4.9 ⭐ | ₹5,512 | ₹16,537 | Direct rates available |
| **Alleppey** | Sterling Lake Palace | 5-star | 4.4 ⭐ | ₹15,387 | ₹30,774 | Live dynamic rates confirmed |

*Room guidance: 2 rooms recommended for 3 adults at each destination.*

### Day-wise Itinerary

- **Day 1 (10 Jan)**: 17:55 Depart Delhi (DEL) → 21:05 Arrive Kochi (COK). Transfer to Hotel Abad Fort. Evening walk by Chinese fishing nets and Kathakali performance.
- **Day 2 (11 Jan)**: Visit Mattancherry Palace and St. Francis Church. Afternoon spice market stroll and seafood dinner.
- **Day 3 (12 Jan)**: Check-out and scenic mountain drive to Munnar (≈260 km, 6–7 hrs). Check-in at Birdwing Cottage; tea garden sunset walk.
- **Day 4 (13 Jan)**: Full day Munnar: Eravikulam National Park, Mattupetty Dam, Echo Point. Traditional Kerala dinner.
- **Day 5 (14 Jan)**: Tea factory tasting tour and local village exploration.
- **Day 6 (15 Jan)**: Check-out and drive to Alleppey (≈140 km, 4–5 hrs). Check-in at Sterling Lake Palace. Afternoon houseboat cruise through the backwaters.
- **Day 7 (16 Jan)**: Backwater village exploration, local spice markets, and farewell seafood dinner.
- **Day 8 (17 Jan)**: Transfer to Cochin Airport (COK). 21:40 Depart on IndiGo 6E2127, arriving Delhi (DEL) at 00:50 (18 Jan).

### Transportation Plan

| Route Segment | Distance | Estimated Duration | Major Highways |
|:---|:---|:---|:---|
| **Kochi → Munnar** | 260 km | 6–7 hrs | NH 47 / NH 85 |
| **Munnar → Alleppey** | 140 km | 4–5 hrs | NH 183 |

### Weather Information
January in Kerala is part of the dry season. Temperatures range from 20 °C to 25 °C, with low humidity and minimal rainfall. Nights in Munnar can be cooler (12 °C–15 °C).

### Food and Activities
- **Kochi**: Appam with fish curry, Kerala biryani, banana chips. Kathakali show, spice market tour, sunset cruise.
- **Munnar**: Fresh tea tastings, local cheese, Munnar honey. Tea plantation walk, wildlife spotting at Eravikulam.
- **Alleppey**: Fresh seafood, puttu with kadala curry. Houseboat cruise, sunset backwater experience.

### Estimated Budget
| Category | Cost (INR) | Pricing Type | Notes |
|:---|:---|:---|:---|
| Flights | ₹69,882.49 | Confirmed | 3 adults, IndiGo roundtrip |
| Accommodation | ₹57,912.00 | Confirmed | 2 rooms each destination |
| Local Transport | ₹5,000.00 | Estimate | Taxis, cabs, transfers |
| Food & Activities | ₹10,000.00 | Estimate | Meals, cultural shows, tours |
| Miscellaneous | ₹5,000.00 | Estimate | Tips, souvenirs, contingencies |
| **Total** | **₹146,794.49** | | **Budget Deficit: ₹56,794.49** (exceeds ₹90,000 budget) |

### Recommendations
- **Packing**: Light, breathable clothing for daytime, a light jacket for evenings in Munnar, comfortable walking shoes.
- **Reservations**: Book flights and accommodation as early as possible to lock in lower rates.
- **Time Management**: Allocate at least 2 hrs for transfers between cities. Arrive at airports 2 hrs before departure.
- **Cash & Cards**: Carry enough cash for small vendors; most hotels and larger restaurants accept cards.

### Important Information
- **Travel Advisories**: No current travel restrictions for Kerala.
- **Permits**: No special permits are required for the destinations listed.
- **Cancellation Policies**: Flights are non-refundable; hotels offer free cancellation up to 48 hrs before check-in.`,
};

