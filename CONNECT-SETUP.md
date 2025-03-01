# AWS Connect Setup Guide

This guide provides instructions on how to set up and utilize AWS Connect after deploying the infrastructure with CDK.

## Table of Contents

- [Accessing AWS Connect](#accessing-aws-connect)
- [Claiming a Phone Number](#claiming-a-phone-number)
- [Creating a Contact Flow](#creating-a-contact-flow)
- [Associating the Phone Number with Your Contact Flow](#associating-the-phone-number-with-your-contact-flow)
- [Setting Up Users (Optional)](#setting-up-users-optional)
- [Testing Your Setup](#testing-your-setup)
- [Important Considerations](#important-considerations)
- [Troubleshooting](#troubleshooting)

## Accessing AWS Connect

After deployment, you'll get an output with the AWS Connect instance URL. It will look something like:
```
https://[instance-id].awsapps.com/connect/
```

1. Navigate to this URL in your browser
2. Sign in with your AWS credentials
3. You'll be taken to the AWS Connect administration console

## Claiming a Phone Number

You'll need to claim a phone number for your Connect instance:

1. In the AWS Connect console, go to "Channels" → "Phone numbers"
2. Click "Claim a number"
3. You have two options:
   - **DID (Direct Inward Dialing)**: Regular phone numbers that customers can call
   - **Toll-free numbers**: Numbers that are free for callers to dial

4. Select your country and choose an available number
5. Give it a description (e.g., "Personal Assistant Line")
6. Click "Save"

## Creating a Contact Flow

A contact flow defines how calls are handled:

1. Go to "Routing" → "Contact flows"
2. Click "Create contact flow"
3. Give it a name like "Personal Assistant Flow"
4. Use the visual editor to build your flow:

   a. **Start Block**: This is where the flow begins
   
   b. **Set Voice**: Add a "Set voice" block to choose the voice for your assistant
      - Connect it to the Start block
      - Choose a voice that sounds natural (e.g., Joanna or Matthew)
      
   c. **Initial Greeting**: Add a "Play prompt" block
      - Connect it to the Set Voice block
      - Add a greeting like "Hello, I'm your personal assistant powered by Claude. How can I help you today?"
      
   d. **Get Customer Input**: Add a "Get customer input" block
      - Connect it to the Initial Greeting block
      - Set the input type to "Speech"
      - Set a timeout (e.g., 5 seconds)
      - Add a prompt like "Please speak after the tone."
      
   e. **Invoke Lambda Function**: Add an "Invoke AWS Lambda function" block
      - Connect it to the Get Customer Input block's "Success" path
      - Select your `connectLambdaIntegration` function
      - In Function input parameters, add a parameter:
        - Key: `SpeechResult`
        - Value: `$.SpeechResult` (this passes the transcribed speech to your Lambda)
      
   f. **Play Response**: Add another "Play prompt" block
      - Connect it to the Invoke Lambda Function block
      - Set the type to "Text to speech"
      - Set the text to `$.External.text` (this will use the SSML response from your Lambda)
      
   g. **Loop Back**: Connect the Play Response block back to the Get Customer Input block to continue the conversation
   
   h. **Error Handling**: Add appropriate error paths from each block to handle timeouts, errors, etc.

5. Save and publish your contact flow

## Associating the Phone Number with Your Contact Flow

1. Go back to "Channels" → "Phone numbers"
2. Select your claimed number
3. In the "Contact flow / IVR" dropdown, select your newly created contact flow
4. Click "Save"

## Setting Up Users (Optional)

If you want to have human agents available as a fallback:

1. Go to "Users" → "User management"
2. Click "Add new users"
3. Fill in the required information
4. Assign appropriate security profiles
5. Create a routing profile to determine how calls are distributed

## Testing Your Setup

1. Call the phone number you claimed
2. Speak to your AI assistant powered by Claude
3. The system should:
   - Capture your speech
   - Send it to your Lambda function
   - Process it with Claude
   - Speak the response back to you

## Important Considerations

### Costs

- **AWS Connect**: Charges per minute of usage
- **Phone Numbers**: Monthly fee for each claimed number
- **Lambda**: Charges based on execution time and memory
- **Secrets Manager**: Monthly fee for storing secrets
- **CloudWatch**: Charges for logs and metrics

### Phone Number Availability

- Availability of phone numbers varies by country and region
- Some countries have regulatory requirements for claiming numbers

### Speech Recognition Quality

- AWS Connect's speech recognition works best with clear speech in supported languages
- Background noise can affect recognition quality
- Consider providing fallback options for misunderstood speech

### Call Recording

- If you want to record calls for quality assurance, you'll need to enable this in your contact flow
- Ensure compliance with applicable laws regarding call recording and notification

### Hours of Operation

- By default, your Connect instance will be available 24/7
- You can set up hours of operation if needed in "Routing" → "Hours of operation"

### Monitoring

- Set up CloudWatch alarms to monitor your Lambda functions and Connect instance
- Monitor costs regularly to avoid unexpected charges

## Troubleshooting

### Lambda Function Errors

If your Lambda function is failing:

1. Check CloudWatch Logs for error messages
2. Verify that the Anthropic API key is correctly stored in Secrets Manager
3. Ensure the Lambda has the correct permissions to access Secrets Manager

### Speech Recognition Issues

If AWS Connect is not correctly recognizing speech:

1. Try adjusting the timeout settings in the "Get customer input" block
2. Consider adding a "Get customer input" block with DTMF (keypad) as a fallback
3. Test in a quiet environment to rule out background noise issues

### Contact Flow Not Working

If your contact flow is not behaving as expected:

1. Use the "Test" feature in the contact flow editor to debug
2. Add logging to your Lambda function to track the flow of data
3. Check that all blocks are correctly connected

### Phone Number Issues

If you're having trouble with your phone number:

1. Verify that the number is correctly associated with your contact flow
2. Check that your AWS account has the necessary permissions for phone numbers
3. Contact AWS Support if the number is not working as expected 