# Calling Bot

## Overview

This folder is for the insurance calling bot feature.

The calling bot is planned as a Twilio-based voice bot for the InsureFlow project. Its job is to help with customer communication during the insurance journey through automated phone calls.

## What We Understood

- The bot should be added inside the project as a separate calling feature.
- Twilio will be used for calling support.
- The screenshot reference showed a voice-agent dashboard with call history, call details, transcripts, analysis, metrics, prompts, tools, voices, and phone-number management.
- For this project, the bot is mainly expected to support customer follow-up and insurance-related communication.

## Primary Direction

The first priority is outbound calling.

Outbound calling fits this project because the system already has:

- incomplete user journeys
- pending forms
- pending payments
- renewals
- follow-up use cases

Inbound calling can also be added later, but the current direction is:

- Phase 1: outbound calling
- Phase 2: inbound + outbound calling

## Inbound vs Outbound

### Inbound Call

The customer calls us.

Example:
- a customer calls the insurance support number to ask about a policy, payment, or plan

### Outbound Call

We call the customer.

Example:
- the bot calls a customer to remind them to complete a form, payment, renewal, or quote journey

## Likely Use Cases In This Project

Based on the current InsureFlow flow, the calling bot can be used for:

- calling customers automatically
- following up on incomplete insurance journeys
- reminding users about pending forms
- reminding users about pending payments
- reminding users about renewals
- explaining insurance plans in a basic guided way
- collecting customer responses over phone
- logging call outcomes for admin review

## Planned Voice Sales Flow

The calling bot is also expected to handle a guided insurance conversation from
interest to data collection.

The expected flow is:

1. The bot introduces the insurance offering to the customer.
2. The bot explains the available insurance plan options.
3. If the customer is interested in buying, the bot continues the journey.
4. The bot asks for the same customer details that are currently collected in
   the form flow.
5. The bot asks for the required coverage amount.
6. Based on the coverage amount, the bot should identify and explain the plans
   that fit that coverage range.
7. The bot continues collecting the remaining journey details until the full
   customer flow is completed.
8. If the insurance purchase is completed successfully through the calling bot,
   the system should generate the policy PDF and send it to the customer's
   email address.

In short, the calling bot should behave like a phone-based insurance assistant
that can:

- explain plans
- qualify customer intent
- collect form data
- ask coverage requirements
- suggest suitable plans
- continue the full customer flow over voice
- trigger policy generation after successful completion
- send the generated policy PDF to the customer email

## What A Mature Calling Bot Dashboard Should Support

From the reference screenshot, these are useful project requirements:

- call history
- call status tracking
- call detail view
- transcript view
- analysis view
- metrics view
- recording status
- agent selection
- prompt management
- tool integration
- voice configuration
- phone-number configuration
- contact or phonebook support

## Important Data To Track

Each call record should ideally store:

- customer name
- customer phone number
- call SID
- call status
- call type
- duration
- cost
- timestamp
- transcript
- analysis or summary
- bot or agent used

## Project Goal

In short, this calling bot should act like an insurance voice agent for:

- follow-up
- reminders
- support
- conversion

It should help the platform communicate with customers more proactively and keep a proper history of all calls and outcomes.

## Current Conclusion

- Twilio is the planned calling provider.
- Outbound calling is the first implementation priority.
- Inbound calling can be added later.
- This feature should eventually include call tracking, transcripts, analytics, and admin visibility.

## Current Implementation Direction

- The backend owner for this feature is `backend/main_backend`.
- The frontend owner for this feature is `frontend/customer_app_frontend`.
- The calling bot is triggered by the customer-app admin.
- The admin can:
  - start an outbound call
  - monitor call records
  - review recommended plans
  - generate a mock payment OTP
  - complete the purchase flow
- Matching plans should come from the existing database-backed quote flow.
- After successful purchase, the policy PDF should be generated and sent to the customer's email.
