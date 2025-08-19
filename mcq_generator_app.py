import streamlit as st
import json
from datetime import datetime
from dotenv import load_dotenv
import os

def configure():
    load_dotenv()
    

# Import Google Gemini SDK (google.generativeai)
import google.generativeai as genai
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")

# Replace with your own Gemini API key
# Get your API key from: https://makersuite.google.com/app/apikey
 # You can put your API key here directly, or use the sidebar input

def initialize_session_state():
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "quiz_generated" not in st.session_state:
        st.session_state.quiz_generated = False
    if "current_step" not in st.session_state:
        st.session_state.current_step = "input"

def generate_questions_with_gemini(topic, num_questions, difficulty, content_input):
    # Check if API key is provided
   
    if not GOOGLE_API_KEY:
        st.error("Google Gemini API key is missing. Please add your API key to continue.")
        st.info("Get your API key from: https://makersuite.google.com/app/apikey")
        return []
    
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Enhanced prompt to avoid generalized questions
        prompt = (
            f"Generate {num_questions} specific, detailed multiple-choice questions on the topic '{topic}' "
            f"at {difficulty} difficulty level. "
            "IMPORTANT REQUIREMENTS:\n"
            "1. Create SPECIFIC questions that test detailed knowledge, NOT general overview questions\n"
            "2. Avoid questions like 'What is the main concept of...', 'What is the primary purpose of...'\n"
            "3. Focus on specific facts, applications, examples, and detailed aspects of the topic\n"
            "4. Each question should test concrete knowledge rather than broad concepts\n"
            "5. Include technical details, specific examples, or practical applications\n\n"
            "Format: Return ONLY a pure JSON array with this exact structure:\n"
            "[{\"question\": \"specific question here\", \"options\": [\"option1\", \"option2\", \"option3\", \"option4\"], \"correct_answer\": 0, \"explanation\": \"detailed explanation here\"}, ...]\n\n"
        )
        
        if content_input.strip():
            prompt += f"Base the questions on this specific content:\n{content_input}\n\n"
        
        prompt += "Return ONLY the JSON array, no markdown formatting, no explanatory text."

        # Use the correct model name
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        content = response.text.strip()

        # Clean up the response
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            questions = json.loads(content)
            
            # Validate the questions structure
            validated_questions = []
            for q in questions:
                if (isinstance(q, dict) and 
                    'question' in q and 
                    'options' in q and 
                    'correct_answer' in q and
                    isinstance(q['options'], list) and
                    len(q['options']) >= 2 and
                    isinstance(q['correct_answer'], int) and
                    0 <= q['correct_answer'] < len(q['options'])):
                    
                    # Ensure explanation exists
                    if 'explanation' not in q:
                        q['explanation'] = "Explanation not provided."
                    
                    validated_questions.append(q)
            
            if validated_questions:
                st.success(f"Successfully generated {len(validated_questions)} questions!")
                return validated_questions
            else:
                st.error("No valid questions were generated. Please try again.")
                return []
                
        except json.JSONDecodeError as e:
            st.error(f"JSON Parse error: {str(e)}")
            st.error(f"Raw Gemini output:\n{content[:500]}...")
            return []
            
    except Exception as e:
        st.error(f"An error occurred with Google Gemini API: {str(e)}")
        st.info("Please check your API key and internet connection.")
        return []

def save_quiz_to_file(questions, quiz_title):
    quiz_data = {
        "quiz_title": quiz_title,
        "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_questions": len(questions),
        "questions": questions,
    }
    return json.dumps(quiz_data, indent=2)

def main():
    configure()
    st.set_page_config(page_title="MCQ Creator", page_icon="📚", layout="wide")

    st.title("📚MCQ Creator")
    st.markdown("*Powered by Google Gemini AI*")
    initialize_session_state()

    with st.sidebar:
        st.header("Configuration")
        
        # API Key input section
        st.warning("API Key Required")
        api_key_input = st.text_input(
            "Enter your Google Gemini API Key:",
            type="password",
            help="Get your API key from https://makersuite.google.com/app/apikey",
            value=GOOGLE_API_KEY if GOOGLE_API_KEY else ""
        )
        if api_key_input:
            # Update the global variable temporarily for this session
            globals()['GOOGLE_API_KEY'] = api_key_input
            st.success("API Key added for this session!")
        elif GOOGLE_API_KEY:
            st.success("API Key configured in code")
            
        st.header("Navigation")
        if st.button("Start New Quiz", type="secondary"):
            st.session_state.questions = []
            st.session_state.quiz_generated = False
            st.session_state.current_step = "input"
            st.rerun()

    if st.session_state.current_step == "input":
        st.header("📝 Quiz Configuration")
        col1, col2 = st.columns(2)
        with col1:
            topic = st.text_input("📖 Enter Topic/Subject",
                                  placeholder="e.g., Python Programming, History, Biology")
            num_questions = st.number_input("📊 Number of Questions",
                                            min_value=1, max_value=20, value=5, step=1)
        with col2:
            difficulty = st.selectbox("🎯 Difficulty Level",
                                      ["Easy", "Medium", "Hard"])
            question_type = st.selectbox("📋 Question Type",
                                         ["Multiple Choice", "True/False", "Mixed"])
        
        st.subheader("Content Input")
        content_input = st.text_area(
            "Paste your content here or describe the topic in detail:",
            height=150,
            placeholder="Enter the specific content you want to create questions from. The more detailed content you provide, the more specific and targeted the questions will be...",
            help="Providing detailed content helps generate specific, non-generalized questions"
        )
        
        # Tips for better questions
        with st.expander("💡 Tips for Better Questions"):
            st.markdown("""
            **To get specific, non-generalized questions:**
            - Provide detailed content about your topic
            - Include specific examples, formulas, or facts
            - Mention particular concepts you want to focus on
            - The more specific your input, the better the questions will be
            
            **Example good inputs:**
            - Specific code snippets for programming topics
            - Detailed historical events with dates and names
            - Scientific formulas and their applications
            - Specific case studies or examples
            """)
        
        if st.button("✨ Generate Questions", type="primary", use_container_width=True):
            if topic and (GOOGLE_API_KEY or globals().get('GOOGLE_API_KEY')):
                with st.spinner("🔄 Generating specific questions..."):
                    current_api_key = GOOGLE_API_KEY or globals().get('GOOGLE_API_KEY', '')
                    if current_api_key:
                        # Temporarily update the API key for this generation
                        original_key = GOOGLE_API_KEY
                        globals()['GOOGLE_API_KEY'] = current_api_key
                        
                        st.session_state.questions = generate_questions_with_gemini(
                            topic, num_questions, difficulty, content_input
                        )
                        
                        # Restore original key
                        globals()['GOOGLE_API_KEY'] = original_key
                        
                        if st.session_state.questions:
                            st.session_state.quiz_generated = True
                            st.session_state.current_step = "generated"
                            st.rerun()
                        else:
                            st.error("Failed to generate questions. Please check your API key and try again.")
                    else:
                        st.error("Please provide your Google Gemini API key.")
            elif not topic:
                st.error("Please enter a topic.")
            else:
                st.error("Please provide your Google Gemini API key.")

    elif st.session_state.current_step == "generated":
        st.header("📋 Generated Quiz Questions")
        if st.session_state.questions:
            quiz_title = st.text_input(
                "📝 Quiz Title",
                value=f"Quiz - {datetime.now().strftime('%Y%m%d_%H%M')}"
            )
            
            for i, q in enumerate(st.session_state.questions, 1):
                with st.expander(f"Question {i}: {q['question'][:50]}...", expanded=True):
                    st.write(f"**{q['question']}**")
                    for j, option in enumerate(q['options']):
                        if j == q['correct_answer']:
                            st.write(f"{chr(65+j)}. {option} *(Correct Answer)*")
                        else:
                            st.write(f"{chr(65+j)}. {option}")
                    if "explanation" in q:
                        st.info(f"💡 **Explanation:** {q['explanation']}")
            
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Generate New Quiz", use_container_width=True):
                    st.session_state.current_step = "input"
                    st.rerun()
            with col2:
                if st.button("✏️ Edit Questions", use_container_width=True):
                    st.info("💡 Edit feature coming soon! For now, regenerate the quiz.")
            with col3:
                if st.button("💾 Save Quiz", type="primary", use_container_width=True):
                    st.session_state.current_step = "saved"
                    st.rerun()

    elif st.session_state.current_step == "saved":
        st.header("💾 Save Your Quiz")
        st.success("Your quiz has been prepared for saving!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Questions", len(st.session_state.questions))
        with col2:
            st.metric("Created", datetime.now().strftime("%Y-%m-%d"))
        with col3:
            st.metric(" Time", datetime.now().strftime("%H:%M"))
        
        quiz_title = st.text_input(
            " Final Quiz Title",
            value=f"My Quiz - {datetime.now().strftime('%Y%m%d_%H%M')}"
        )
        
        with st.expander(" Preview Questions", expanded=False):
            for i, q in enumerate(st.session_state.questions, 1):
                st.write(f"**{i}. {q['question']}**")
                for j, option in enumerate(q['options']):
                    marker = "✅" if j == q["correct_answer"] else "⚪"
                    st.write(f"   {marker} {chr(65+j)}. {option}")
                st.markdown("---")
        
        st.subheader("💾 Save Options")
        col1, col2 = st.columns(2)
        with col1:
            quiz_json = save_quiz_to_file(st.session_state.questions, quiz_title)
            filename_json = f"{quiz_title.replace(' ', '_')}.json"
            st.download_button(
                label="📥 Download as JSON",
                data=quiz_json,
                file_name=filename_json,
                mime="application/json",
                use_container_width=True
            )
        with col2:
            text_content = f"{quiz_title}\n{'='*50}\n\n"
            for i, q in enumerate(st.session_state.questions, 1):
                text_content += f"Question {i}: {q['question']}\n"
                for j, option in enumerate(q['options']):
                    marker = "[✓]" if j == q["correct_answer"] else "[ ]"
                    text_content += f"  {marker} {chr(65+j)}. {option}\n"
                if "explanation" in q:
                    text_content += f"  Explanation: {q['explanation']}\n"
                text_content += "\n"
            st.download_button(
                label="📄 Download as Text",
                data=text_content,
                file_name=f"{quiz_title.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Create Another Quiz", use_container_width=True):
                st.session_state.questions = []
                st.session_state.quiz_generated = False
                st.session_state.current_step = "input"
                st.rerun()
        with col2:
            if st.button("⬅️ Back to Quiz", use_container_width=True):
                st.session_state.current_step = "generated"
                st.rerun()
        with col3:
            if st.button("✨ Generate More Questions", use_container_width=True):
                st.session_state.current_step = "input"
                st.rerun()
        
        st.markdown("---")
        st.success("🎉 **Quiz saved successfully!** You can download it in your preferred format above.")
        st.info("💡 **Tip:** Your quiz data is preserved in this session. Use the buttons above to navigate or create new quizzes.")

if __name__ == "__main__":
    if "questions" not in st.session_state:
        st.session_state.questions = []
    main()