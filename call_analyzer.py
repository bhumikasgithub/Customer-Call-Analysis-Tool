import os
from groq import Groq
import csv
from flask import Flask, request, render_template_string, redirect, url_for
import json

# Initialize Flask app
app = Flask(__name__)

# Initialize Groq client
# You need to set your Groq API key as an environment variable
# Get your free API key from: https://console.groq.com/
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Customer Call Analysis</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }
        textarea { width: 100%; height: 200px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #4CAF50; color: white; padding: 15px 32px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #45a049; }
        .result { background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .error { background: #ffebee; color: #c62828; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Customer Call Analysis Tool</h1>
    
    <div class="container">
        <h2>Enter Customer Call Transcript:</h2>
        <form method="POST" action="/analyze">
            <textarea name="transcript" placeholder="Paste your customer call transcript here...
            
Example:
Customer: Hi, I was trying to book a slot yesterday but the payment failed. I've been trying for hours and I'm really frustrated.
Agent: I'm sorry to hear about the payment issue. Let me check your account and help resolve this right away.
Customer: Thank you, I really need this booking confirmed today."></textarea>
            <br><br>
            <button type="submit">Analyze Call</button>
        </form>
    </div>

    {% if result %}
    <div class="container">
        <h2>Analysis Results:</h2>
        <div class="result">
            <h3>Original Transcript:</h3>
            <p>{{ result.transcript }}</p>
            
            <h3>Summary:</h3>
            <p>{{ result.summary }}</p>
            
            <h3>Sentiment:</h3>
            <p>{{ result.sentiment }}</p>
        </div>
        <p><strong>✅ Results saved to call_analysis.csv</strong></p>
    </div>
    {% endif %}

    {% if error %}
    <div class="error">
        <strong>Error:</strong> {{ error }}
    </div>
    {% endif %}

    <div class="container">
        <h3>Instructions:</h3>
        <ol>
            <li>Get a free Groq API key from <a href="https://console.groq.com/" target="_blank">https://console.groq.com/</a></li>
            <li>Set your API key as environment variable: <code>GROQ_API_KEY=your_key_here</code></li>
            <li>Paste any customer conversation in the text area above</li>
            <li>Click "Analyze Call" to get summary and sentiment</li>
            <li>Results will be automatically saved to call_analysis.csv</li>
        </ol>
    </div>
</body>
</html>
"""

def analyze_with_groq(transcript):
    """
    Use Groq API to analyze the transcript
    Returns summary and sentiment
    """
    try:
        # Get summary
        summary_response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize this customer call transcript in 2-3 sentences:\n\n{transcript}"
                }
            ],
            model="llama-3.1-8b-instant",  # Using Llama 3 model
        )
        summary = summary_response.choices[0].message.content.strip()
        
        # Get sentiment
        sentiment_response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze the sentiment of this customer call transcript. Respond with only one word: 'Positive', 'Negative', or 'Neutral':\n\n{transcript}"
                }
            ],
            model="llama-3.1-8b-instant",
        )
        sentiment = sentiment_response.choices[0].message.content.strip()
        
        return summary, sentiment
    
    except Exception as e:
        raise Exception(f"Groq API error: {str(e)}")

def save_to_csv(transcript, summary, sentiment):
    """
    Save the analysis results to a CSV file
    """
    filename = "call_analysis.csv"
    
    # Check if file exists to write headers
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write headers if file is new
        if not file_exists:
            writer.writerow(['Transcript', 'Summary', 'Sentiment'])
        
        # Write the data
        writer.writerow([transcript, summary, sentiment])

@app.route('/')
def home():
    """Main page with the form"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Process the transcript and return results"""
    try:
        # Get transcript from form
        transcript = request.form.get('transcript', '').strip()
        
        if not transcript:
            return render_template_string(HTML_TEMPLATE, error="Please enter a transcript!")
        
        # Check if API key is set
        if not os.environ.get("GROQ_API_KEY"):
            return render_template_string(HTML_TEMPLATE, 
                error="Please set your GROQ_API_KEY environment variable!")
        
        # Analyze with Groq
        summary, sentiment = analyze_with_groq(transcript)
        
        # Save to CSV
        save_to_csv(transcript, summary, sentiment)
        
        # Show results
        result = {
            'transcript': transcript,
            'summary': summary,
            'sentiment': sentiment
        }
        
        print("\n" + "="*50)
        print("ANALYSIS RESULTS")
        print("="*50)
        print(f"Original Transcript:\n{transcript}")
        print(f"\nSummary:\n{summary}")
        print(f"\nSentiment: {sentiment}")
        print("="*50)
        print("✅ Results saved to call_analysis.csv")
        print("="*50)
        
        return render_template_string(HTML_TEMPLATE, result=result)
        
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=str(e))

if __name__ == '__main__':
    print("🚀 Starting Customer Call Analysis Server...")
    print("📝 Make sure you have set your GROQ_API_KEY environment variable!")
    print("🌐 Server will run at: http://localhost:5000")
    print("📊 Results will be saved to: call_analysis.csv")
    print("-" * 50)
    
    app.run(debug=True, host='localhost', port=5000)