# Auction & Trade

## Overview
The Auction & Trade subsystem facilitates item exchange between players via auction systems. It supports bidding, item tracking, timed sales, and transaction processing with notification and cancellation features, providing a robust player-driven economy. This system creates an interactive marketplace where players can buy and sell items without requiring direct interaction, expanding economic opportunities beyond standard NPC merchant shops.

## Responsibilities
- Managing player-to-player item sales via auction
- Handling bidding mechanics and timing
- Processing transactions and item transfers
- Providing notifications and auction status updates
- Supporting auction cancellation and validation
- Maintaining auction state across server restarts
- Preventing auction abuse and scamming
- Enabling player economic interaction

## Core Components

### Auction System
- `Auction`: Player-to-player item sale mechanism
  - Manages bidding and timing for item auctions
  - Handles transaction processing for sold items
  - Provides notifications for auction participants
  - Supports auction cancellation with proper rules
  - Maintains auction state throughout the process
  - Implements multi-stage countdown with notifications
  - Enforces validation rules for acceptable items
  - Controls minimum bid increments

### Trade Implementation
- **Bidding Mechanics**: System for placing and tracking bids
  - Minimum bid requirements
  - Bid increment rules
  - Last-minute extension logic
  - Historical bid tracking

- **Transaction Processing**: Handling of successful auctions
  - Item transfer to winning bidder
  - Gold transfer to seller
  - Fee collection if applicable
  - Inventory management
  - Failed transaction handling

- **Notification System**: Keeping participants informed
  - New auction announcements
  - Bid updates and outbid notifications
  - Countdown warnings
  - Completion notifications
  - Cancellation alerts

### Additional Features
- **Auction Channel**: Dedicated communication channel for auction updates
- **Item Validation**: Checks to ensure items can be auctioned
- **Bid Validation**: Verification that bidders have sufficient funds
- **Cancel Logic**: Rules for when and how auctions can be cancelled

## Implementation Details

### Auction Process
- **Starting an Auction**: Player puts item up for sale with minimum bid
- **Bidding Period**: Other players can place bids on the item
- **Countdown System**: Multiple countdown stages with notifications
- **Completion**: Winner determined, items and gold transferred
- **Cancellation**: Rules for seller to cancel under certain conditions
- **Failed Auction**: Handling when no bids are received

### Transaction Processing
- **Bid Placement**: Validating and recording player bids
- **Fund Verification**: Ensuring bidders have sufficient gold
- **Item Transfer**: Moving the item from seller to buyer
- **Payment Processing**: Transferring gold from buyer to seller
- **Auction Fees**: Optional taxation of auction transactions

## Key Files

### Header Files
- `/src/include/Auction.hh` (31 LOC) - Auction system interface
  - Defines the Auction class structure
  - Declares auction state management functions 
  - Contains auction timing parameters

### Implementation Files
- `/src/Auction.cc` - Implementation of auction functionality
  - Contains bidding logic and validation
  - Implements countdown and timing system
  - Handles transaction completion
  - Manages auction notification system

- Related command implementations in command files
  - Auction starting commands
  - Bidding command handlers
  - Auction information commands
  - Auction cancellation commands

## System Behaviors

### Core Behaviors
- **Auction Listing**: Players can place items up for auction
- **Bidding**: Interested players can place bids on auctioned items
- **Timed Countdown**: Auctions progress through timed stages
- **Auto-completion**: System automatically resolves completed auctions
- **Broadcast Notifications**: Major auction events are announced

### Special Features
- **Auction Channel**: Dedicated channel for auction-related messages
- **Bid History**: Tracking of bid history for each auction
- **Last-call Extensions**: Time extensions for late bidding
- **Item Inspection**: Ability to examine auctioned items
- **Minimum Increments**: Required minimum bid increases
- **Reserve Prices**: Minimum threshold for successful auctions

## Dependencies and Relationships

### Dependencies On
- **Object System**: For items being auctioned, their properties and transfer
- **Character System**: For player data, inventory, and gold management
- **Command Interpreter**: For auction and bidding commands
- **Communication System**: For auction announcements and notifications
- **Economy System**: For gold transfers and economic balance

### Depended On By
- **Player Economy**: Creates a player-driven marketplace
- **Item Distribution**: Provides alternative means of obtaining items
- **Gold Sink**: Potentially removes currency from economy through fees
- **Social Trading**: Enables economic interaction between players

## Future Improvements
- Add more auction types including sealed bid auctions
- Implement buyout option for immediate purchase
- Enhance notification system with more detailed tracking
- Create auction search and filtering features
- Integrate with a more formal shop and barter system
- Add auction house locations in major cities
- Implement auction item categories and sorting
- Create scheduled specialty auctions for rare items
- Develop auction statistics and market trend tracking
