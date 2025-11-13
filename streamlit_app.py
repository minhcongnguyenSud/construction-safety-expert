"""Streamlit web interface for Corporate Safety Agent."""

import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

from orchestrator import CorporateSafetyAgent
from orchestrator.document_processor import DocumentProcessor
from orchestrator.pdf_categorizer import PDFCategorizer
from orchestrator.llm_provider import get_available_models, get_provider_info, get_llm
from orchestrator.claude_skills_provider import ClaudeSkillsProvider

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Corporate Safety Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .skill-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 600;
        font-size: 0.875rem;
        margin: 0.25rem;
    }
    .fall-badge {
        background-color: #fef3c7;
        color: #92400e;
    }
    .electrical-badge {
        background-color: #dbeafe;
        color: #1e40af;
    }
    .struckby-badge {
        background-color: #fce7f3;
        color: #9f1239;
    }
    .general-badge {
        background-color: #e5e7eb;
        color: #374151;
    }
    .answer-box {
        background-color: #f9fafb;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .sources-box {
        background-color: #eff6ff;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
        font-size: 0.875rem;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_agent():
    """Initialize the safety agent."""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        st.error("⚠️ ANTHROPIC_API_KEY not found in environment variables.")
        st.info("Please set your API key in the sidebar or create a .env file.")
        return None

    try:
        agent = CorporateSafetyAgent(api_key=api_key)
        return agent
    except Exception as e:
        st.error(f"Error initializing agent: {e}")
        return None


def get_skill_badge(skill_name):
    """Get HTML badge for skill."""
    skill_lower = skill_name.lower()

    if "fall" in skill_lower:
        return '<span class="skill-badge fall-badge">🪜 Fall Hazard</span>'
    elif "electrical" in skill_lower:
        return '<span class="skill-badge electrical-badge">⚡ Electrical Hazard</span>'
    elif "struck" in skill_lower:
        return '<span class="skill-badge struckby-badge">🚧 Struck-By Hazard</span>'
    else:
        return '<span class="skill-badge general-badge">📋 General Safety</span>'


def main():
    """Main Streamlit application."""

    # Header
    st.markdown('<h1 class="main-header">🛡️ Corporate Safety Agent</h1>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #6b7280; margin-bottom: 2rem;'>"
        "AI-powered workplace safety assistant using RAG and Claude"
        "</p>",
        unsafe_allow_html=True
    )

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Mode selection - NEW!
        st.subheader("🎯 Inference Mode")
        mode_option = st.radio(
            "Select inference mode:",
            ["Custom RAG", "Claude Skills"],
            help="Custom RAG: Your orchestrator with FAISS vector search\nClaude Skills: Claude Code managed skills for comparison"
        )

        if mode_option == "Claude Skills":
            st.info("🔬 **Comparison Mode**: Using Claude Code managed skills with prompt-based expertise")
        else:
            st.info("🏗️ **Custom Mode**: Using your RAG orchestrator with vector search")

        st.divider()

        # Provider selection (only for Custom RAG mode)
        if mode_option == "Custom RAG":
            provider_option = st.selectbox(
                "AI Provider",
                ["anthropic", "openai"],
                format_func=lambda x: f"{get_provider_info(x).get('icon', '🤖')} {get_provider_info(x).get('name', x)}",
                help="Select the AI provider to use"
            )
        else:
            provider_option = "anthropic"  # Claude Skills only works with Anthropic

        provider_info = get_provider_info(provider_option)

        # API Key input (optional override)
        api_key_label = f"{provider_info.get('name', 'API')} Key (optional)"
        api_key_help = f"Leave empty to use {provider_info.get('env_var', 'API_KEY')} from environment"

        api_key_input = st.text_input(
            api_key_label,
            type="password",
            help=api_key_help
        )

        if api_key_input:
            os.environ[provider_info.get('env_var', 'API_KEY')] = api_key_input

        st.divider()

        # Model selection based on provider (only for Custom RAG mode)
        if mode_option == "Custom RAG":
            available_models = get_available_models(provider_option)
            model_option = st.selectbox(
                f"{provider_info.get('name', 'Model')} Model",
                available_models,
                help=f"Select the {provider_info.get('name', 'model')} to use"
            )
        else:
            model_option = "claude-3-haiku-20240307"  # Fixed model for Claude Skills (Haiku)
            st.text(f"Model: {model_option}")

        st.divider()

        # Available Skills
        st.header("🎯 Available Skills")
        st.markdown("""
        <div style="padding: 0.5rem;">
        <div style="margin-bottom: 0.5rem;">🪜 <strong>Fall Hazards</strong></div>
        <div style="font-size: 0.875rem; color: #6b7280; margin-left: 1.5rem;">
        Heights, ladders, scaffolding, fall protection
        </div>
        </div>

        <div style="padding: 0.5rem;">
        <div style="margin-bottom: 0.5rem;">⚡ <strong>Electrical Hazards</strong></div>
        <div style="font-size: 0.875rem; color: #6b7280; margin-left: 1.5rem;">
        Lockout/tagout, power lines, arc flash
        </div>
        </div>

        <div style="padding: 0.5rem;">
        <div style="margin-bottom: 0.5rem;">🚧 <strong>Struck-By Hazards</strong></div>
        <div style="font-size: 0.875rem; color: #6b7280; margin-left: 1.5rem;">
        Vehicles, falling objects, rigging
        </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Example Questions
        st.header("💡 Example Questions")

        example_questions = {
            "🪜 Fall Protection": "What safety equipment is needed for working at heights?",
            "⚡ Lockout/Tagout": "What is lockout/tagout and when should it be used?",
            "🚧 Falling Objects": "How can I prevent being hit by falling objects?",
            "🪜 Ladder Safety": "How do I properly set up a ladder?",
            "⚡ Power Lines": "How far should I stay from power lines?",
            "🚧 Forklift Safety": "What safety measures are needed around forklifts?"
        }

        for label, question in example_questions.items():
            if st.button(label, key=label, use_container_width=True):
                st.session_state.selected_example = question

        st.divider()

        # PDF Upload Section
        st.header("📄 Upload Knowledge Base")

        uploaded_file = st.file_uploader(
            "Upload Safety Document",
            type=['pdf', 'docx', 'doc', 'txt'],
            help="Upload safety documents - AI will divide into sections, categorize each section, and add to current knowledge base"
        )

        if uploaded_file:
            if st.button("Process Document", type="primary", use_container_width=True):
                # Check if document was already imported
                from orchestrator.knowledge_base_manager import KnowledgeBaseManager
                kb_manager = KnowledgeBaseManager()

                if kb_manager.is_document_imported(uploaded_file.name):
                    st.warning(f"⏭️  Document '{uploaded_file.name}' has already been imported!")
                    st.info("This document was previously processed. Skipping to avoid duplicates.")

                    # Show when it was imported
                    metadata = kb_manager._load_metadata()
                    import_info = metadata["imported_documents"].get(uploaded_file.name, {})
                    if import_info:
                        st.write(f"   • Imported: {import_info.get('imported_at', 'Unknown date')}")
                        st.write(f"   • Category: {import_info.get('category', 'Unknown')}")
                        st.write(f"   • Chunks added: {import_info.get('chunks_added', 0)}")
                else:
                    with st.spinner(f"📄 Processing {uploaded_file.name}..."):
                        try:
                            # Save uploaded file temporarily with correct extension
                            file_extension = uploaded_file.name.split('.')[-1]
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                tmp_path = tmp_file.name

                            # Process document
                            processor = DocumentProcessor()
                            chunks = processor.process_document(tmp_path, "general")

                            # Auto-categorize using LLM
                            st.info("🤖 AI is analyzing and categorizing each chunk...")
                            api_key = os.getenv(provider_info.get('env_var', 'API_KEY'))
                            llm = get_llm(provider=provider_option, api_key=api_key, temperature=0)
                            categorizer = PDFCategorizer(llm)
                            categorized_chunks = categorizer.categorize_chunks(chunks, llm)

                            # Create knowledge_base directory if it doesn't exist
                            kb_dir = "knowledge_base"
                            os.makedirs(kb_dir, exist_ok=True)

                            # Append chunks to existing base knowledge files (with deduplication)
                            saved_categories = []
                            total_saved = 0
                            total_skipped = 0

                            for category, cat_chunks in categorized_chunks.items():
                                if cat_chunks:
                                    # Path to existing base knowledge file (now using JSON)
                                    base_file = os.path.join(kb_dir, f"{category}_base.json")

                                    if os.path.exists(base_file):
                                        # Count before adding
                                        before_count = len(kb_manager.load_knowledge_base(category))

                                        processor.append_chunks_to_base_file(cat_chunks, base_file)

                                        # Count after adding to see how many were actually added
                                        after_count = len(kb_manager.load_knowledge_base(category))
                                        actually_added = after_count - before_count
                                        skipped = len(cat_chunks) - actually_added

                                        saved_categories.append(f"{category}: {actually_added} sections added" +
                                                              (f", {skipped} duplicates skipped" if skipped > 0 else ""))
                                        total_saved += actually_added
                                        total_skipped += skipped
                                    else:
                                        st.warning(f"⚠️ Base file not found: {base_file}")

                            # Record that this document has been imported
                            kb_manager.record_document_import(
                                uploaded_file.name,
                                category="mixed",  # Could be multiple categories
                                chunks_added=total_saved
                            )

                            # Clean up temp file
                            os.unlink(tmp_path)

                            st.success(f"✅ Added {total_saved} new sections from {uploaded_file.name}")
                            if total_skipped > 0:
                                st.info(f"⏭️  Skipped {total_skipped} duplicate sections")
                            st.info("📁 Sections added to categories:")
                            for category_info in saved_categories:
                                st.write(f"   • {category_info}")
                            st.warning("⚠️ Please restart the app to load the updated knowledge base")

                        except Exception as e:
                            st.error(f"❌ Error processing document: {str(e)}")

    # Initialize session state
    if 'agent' not in st.session_state:
        with st.spinner("🔄 Initializing Corporate Safety Agent..."):
            if mode_option == "Custom RAG":
                st.session_state.agent = initialize_agent()
            else:  # Claude Skills mode
                api_key = os.getenv("ANTHROPIC_API_KEY")
                try:
                    st.session_state.agent = ClaudeSkillsProvider(api_key=api_key)
                except Exception as e:
                    st.error(f"❌ Failed to initialize Claude Skills: {str(e)}")
                    st.session_state.agent = None

            st.session_state.model = model_option
            st.session_state.provider = provider_option
            st.session_state.mode = mode_option

    # Reinitialize agent if mode, model, or provider changes
    config_changed = (
        ('mode' in st.session_state and st.session_state.mode != mode_option) or
        ('model' in st.session_state and st.session_state.model != model_option) or
        ('provider' in st.session_state and st.session_state.provider != provider_option)
    )

    if config_changed:
        mode_display = "Claude Skills" if mode_option == "Claude Skills" else f"{provider_info.get('name', provider_option)} - {model_option}"
        with st.spinner(f"🔄 Switching to {mode_display}..."):
            api_key = os.getenv(provider_info.get('env_var', 'API_KEY'))
            try:
                if mode_option == "Custom RAG":
                    st.session_state.agent = CorporateSafetyAgent(
                        api_key=api_key,
                        model=model_option,
                        provider=provider_option
                    )
                else:  # Claude Skills mode
                    st.session_state.agent = ClaudeSkillsProvider(api_key=api_key)

                st.session_state.model = model_option
                st.session_state.provider = provider_option
                st.session_state.mode = mode_option
                st.success(f"✅ Switched to {mode_display}")
            except Exception as e:
                st.error(f"❌ Failed to switch: {str(e)}")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'selected_example' not in st.session_state:
        st.session_state.selected_example = None

    # Main content area
    if st.session_state.agent is None:
        st.warning("⚠️ Please configure your Anthropic API key to continue.")
        st.info("👈 Enter your API key in the sidebar or set the ANTHROPIC_API_KEY environment variable.")
        return

    # Chat interface
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("💬 Ask a Safety Question")

    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.selected_example = None
            st.rerun()

    # Question input
    default_question = st.session_state.selected_example if st.session_state.selected_example else ""
    question = st.text_area(
        "Your question:",
        value=default_question,
        height=100,
        placeholder="Example: What are the requirements for scaffolding safety?",
        key="question_input"
    )

    # Reset selected example after use
    if st.session_state.selected_example:
        st.session_state.selected_example = None

    # Submit button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        submit_button = st.button("🚀 Ask Question", type="primary", use_container_width=True)
    with col2:
        compare_button = st.button("⚖️ Compare Modes", use_container_width=True)

    # Process question
    if submit_button and question.strip():
        with st.spinner("🤔 Processing your question..."):
            try:
                result = st.session_state.agent.ask(question)

                # Add to chat history
                st.session_state.chat_history.append({
                    'question': question,
                    'result': result
                })

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # Compare modes side-by-side
    if compare_button and question.strip():
        st.divider()
        st.header("⚖️ Mode Comparison")
        st.markdown(f"**Question:** {question}")

        col_custom, col_claude = st.columns(2)

        # Custom RAG Mode
        with col_custom:
            st.subheader("🏗️ Custom RAG")
            with st.spinner("Processing with Custom RAG..."):
                try:
                    api_key = os.getenv("ANTHROPIC_API_KEY")
                    custom_agent = CorporateSafetyAgent(
                        api_key=api_key,
                        model="claude-3-haiku-20240307",
                        provider="anthropic"
                    )
                    custom_result = custom_agent.ask(question)

                    st.markdown(f"**Skill:** {custom_result['skill']}")
                    st.markdown(f"**Mode:** {custom_result.get('mode', 'custom-rag')}")
                    st.markdown("**Answer:**")
                    st.markdown(f"<div style='background-color: #f0f9ff; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #0284c7;'>{custom_result['answer']}</div>", unsafe_allow_html=True)
                    st.markdown(f"**Sources:** {', '.join(custom_result['sources'][:3])}")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        # Claude Skills Mode
        with col_claude:
            st.subheader("🔬 Claude Skills")
            with st.spinner("Processing with Claude Skills..."):
                try:
                    api_key = os.getenv("ANTHROPIC_API_KEY")
                    claude_agent = ClaudeSkillsProvider(api_key=api_key)
                    claude_result = claude_agent.ask(question)

                    st.markdown(f"**Skill:** {claude_result['skill']}")
                    st.markdown(f"**Mode:** {claude_result.get('mode', 'claude-skills')}")
                    st.markdown("**Answer:**")
                    st.markdown(f"<div style='background-color: #f0fdf4; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #16a34a;'>{claude_result['answer']}</div>", unsafe_allow_html=True)
                    st.markdown(f"**Sources:** {', '.join(claude_result['sources'][:3])}")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Display chat history (most recent first)
    if st.session_state.chat_history:
        st.divider()
        st.header("📜 Conversation History")

        for idx, chat in enumerate(reversed(st.session_state.chat_history)):
            with st.container():
                # Question
                st.markdown(f"### 🙋 Question {len(st.session_state.chat_history) - idx}")
                st.markdown(f"**{chat['question']}**")

                # Skill badge
                st.markdown(get_skill_badge(chat['result']['skill']), unsafe_allow_html=True)

                # Mode badge
                mode_display = chat['result'].get('mode', 'custom-rag')
                if mode_display == 'claude-skills':
                    st.markdown('<span style="background-color: #dcfce7; color: #166534; padding: 0.25rem 0.75rem; border-radius: 1rem; font-weight: 600; font-size: 0.875rem; margin-left: 0.5rem;">🔬 Claude Skills Mode</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span style="background-color: #e0e7ff; color: #3730a3; padding: 0.25rem 0.75rem; border-radius: 1rem; font-weight: 600; font-size: 0.875rem; margin-left: 0.5rem;">🏗️ Custom RAG Mode</span>', unsafe_allow_html=True)

                # Answer
                st.markdown('<div class="answer-box">', unsafe_allow_html=True)
                st.markdown(f"**🤖 {chat['result']['skill']}:**")
                st.markdown(chat['result']['answer'])
                st.markdown('</div>', unsafe_allow_html=True)

                # Sources
                if chat['result'].get('sources'):
                    st.markdown('<div class="sources-box">', unsafe_allow_html=True)
                    st.markdown(f"**📚 Sources:** {', '.join(chat['result']['sources'])}")
                    st.markdown('</div>', unsafe_allow_html=True)

                # Metadata
                with st.expander("ℹ️ Details"):
                    st.json({
                        'skill': chat['result']['skill'],
                        'routed_to': chat['result']['routed_to'],
                        'sources': chat['result']['sources']
                    })

                st.divider()
    else:
        # Welcome message
        st.info("""
        👋 **Welcome to the Corporate Safety Agent!**

        Ask me questions about workplace safety, and I'll route your question to the appropriate expert skill:
        - 🪜 **Fall Hazards** - Working at heights, ladders, scaffolding
        - ⚡ **Electrical Hazards** - Lockout/tagout, power lines, electrical safety
        - 🚧 **Struck-By Hazards** - Vehicles, falling objects, material handling

        Click an example question in the sidebar to get started!
        """)


if __name__ == "__main__":
    main()
