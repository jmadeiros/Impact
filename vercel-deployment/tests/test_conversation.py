"""
Unit tests for Conversational RAG components
Tests conversation management, session handling, and conversational flow
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from conversation import (
    ConversationTurn, ConversationSession, ServerlessConversationManager,
    ConversationalRAGAdapter, create_conversational_rag
)


class TestConversationTurn(unittest.TestCase):
    """Test cases for ConversationTurn dataclass"""
    
    def test_conversation_turn_creation(self):
        """Test creating a conversation turn"""
        turn = ConversationTurn(
            timestamp="2024-01-01T12:00:00",
            user_message="How do programs build confidence?",
            assistant_response="Programs build confidence through...",
            evidence_count=3,
            organizations=["YCUK", "Palace for Life"],
            age_groups=["16-18"],
            processing_time=2.5
        )
        
        self.assertEqual(turn.timestamp, "2024-01-01T12:00:00")
        self.assertEqual(turn.user_message, "How do programs build confidence?")
        self.assertEqual(turn.assistant_response, "Programs build confidence through...")
        self.assertEqual(turn.evidence_count, 3)
        self.assertEqual(turn.organizations, ["YCUK", "Palace for Life"])
        self.assertEqual(turn.age_groups, ["16-18"])
        self.assertEqual(turn.processing_time, 2.5)


class TestConversationSession(unittest.TestCase):
    """Test cases for ConversationSession dataclass"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_turn = ConversationTurn(
            timestamp="2024-01-01T12:00:00",
            user_message="Test message",
            assistant_response="Test response",
            evidence_count=1,
            organizations=["Test Org"],
            age_groups=["16-18"],
            processing_time=1.0
        )
    
    def test_conversation_session_creation(self):
        """Test creating a conversation session"""
        session = ConversationSession(
            session_id="test_session",
            created_at="2024-01-01T10:00:00",
            last_activity="2024-01-01T12:00:00",
            turns=[self.test_turn],
            context_summary="Test context"
        )
        
        self.assertEqual(session.session_id, "test_session")
        self.assertEqual(session.created_at, "2024-01-01T10:00:00")
        self.assertEqual(session.last_activity, "2024-01-01T12:00:00")
        self.assertEqual(len(session.turns), 1)
        self.assertEqual(session.context_summary, "Test context")
    
    def test_session_to_dict(self):
        """Test converting session to dictionary"""
        session = ConversationSession(
            session_id="test_session",
            created_at="2024-01-01T10:00:00",
            last_activity="2024-01-01T12:00:00",
            turns=[self.test_turn]
        )
        
        session_dict = session.to_dict()
        
        self.assertIsInstance(session_dict, dict)
        self.assertEqual(session_dict['session_id'], "test_session")
        self.assertEqual(len(session_dict['turns']), 1)
        self.assertIsInstance(session_dict['turns'][0], dict)
    
    def test_session_from_dict(self):
        """Test creating session from dictionary"""
        session_data = {
            'session_id': 'test_session',
            'created_at': '2024-01-01T10:00:00',
            'last_activity': '2024-01-01T12:00:00',
            'turns': [
                {
                    'timestamp': '2024-01-01T12:00:00',
                    'user_message': 'Test message',
                    'assistant_response': 'Test response',
                    'evidence_count': 1,
                    'organizations': ['Test Org'],
                    'age_groups': ['16-18'],
                    'processing_time': 1.0
                }
            ],
            'context_summary': 'Test context'
        }
        
        session = ConversationSession.from_dict(session_data)
        
        self.assertEqual(session.session_id, 'test_session')
        self.assertEqual(len(session.turns), 1)
        self.assertIsInstance(session.turns[0], ConversationTurn)
        self.assertEqual(session.turns[0].user_message, 'Test message')


class TestServerlessConversationManager(unittest.TestCase):
    """Test cases for ServerlessConversationManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = ServerlessConversationManager(
            max_turns_per_session=5,
            session_timeout_hours=1
        )
        self.session_id = "test_session"
    
    def test_initialization(self):
        """Test conversation manager initialization"""
        self.assertEqual(self.manager.max_turns_per_session, 5)
        self.assertEqual(self.manager.session_timeout_hours, 1)
        self.assertEqual(self.manager._sessions, {})
    
    def test_create_session(self):
        """Test creating a new session"""
        session = self.manager.create_session(self.session_id)
        
        self.assertEqual(session.session_id, self.session_id)
        self.assertEqual(len(session.turns), 0)
        self.assertIn(self.session_id, self.manager._sessions)
        
        # Timestamps should be recent
        created_time = datetime.fromisoformat(session.created_at)
        self.assertLess(datetime.now() - created_time, timedelta(seconds=5))
    
    def test_get_existing_session(self):
        """Test getting an existing session"""
        # Create session first
        original_session = self.manager.create_session(self.session_id)
        
        # Get the same session
        retrieved_session = self.manager.get_session(self.session_id)
        
        self.assertEqual(retrieved_session.session_id, original_session.session_id)
        self.assertEqual(retrieved_session.created_at, original_session.created_at)
    
    def test_get_nonexistent_session(self):
        """Test getting a non-existent session"""
        session = self.manager.get_session("nonexistent_session")
        self.assertIsNone(session)
    
    def test_session_expiration(self):
        """Test session expiration based on timeout"""
        # Create session
        session = self.manager.create_session(self.session_id)
        
        # Manually set last_activity to expired time
        expired_time = datetime.now() - timedelta(hours=2)
        session.last_activity = expired_time.isoformat()
        
        # Try to get expired session
        retrieved_session = self.manager.get_session(self.session_id)
        
        self.assertIsNone(retrieved_session)
        self.assertNotIn(self.session_id, self.manager._sessions)
    
    def test_add_turn_new_session(self):
        """Test adding a turn to a new session"""
        session = self.manager.add_turn(
            session_id=self.session_id,
            user_message="How do programs help?",
            assistant_response="Programs help by...",
            evidence_count=3,
            organizations=["YCUK"],
            age_groups=["16-18"],
            processing_time=2.1
        )
        
        self.assertEqual(session.session_id, self.session_id)
        self.assertEqual(len(session.turns), 1)
        
        turn = session.turns[0]
        self.assertEqual(turn.user_message, "How do programs help?")
        self.assertEqual(turn.assistant_response, "Programs help by...")
        self.assertEqual(turn.evidence_count, 3)
        self.assertEqual(turn.organizations, ["YCUK"])
        self.assertEqual(turn.age_groups, ["16-18"])
        self.assertEqual(turn.processing_time, 2.1)
    
    def test_add_turn_existing_session(self):
        """Test adding a turn to an existing session"""
        # Create session with first turn
        session = self.manager.add_turn(
            session_id=self.session_id,
            user_message="First message",
            assistant_response="First response",
            evidence_count=1,
            organizations=["Org1"],
            age_groups=["13-15"],
            processing_time=1.0
        )
        
        # Add second turn
        session = self.manager.add_turn(
            session_id=self.session_id,
            user_message="Second message",
            assistant_response="Second response",
            evidence_count=2,
            organizations=["Org2"],
            age_groups=["16-18"],
            processing_time=1.5
        )
        
        self.assertEqual(len(session.turns), 2)
        self.assertEqual(session.turns[0].user_message, "First message")
        self.assertEqual(session.turns[1].user_message, "Second message")
    
    def test_turn_limit_enforcement(self):
        """Test that turn limit is enforced"""
        # Add more turns than the limit (5)
        for i in range(7):
            self.manager.add_turn(
                session_id=self.session_id,
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
                evidence_count=1,
                organizations=["Test Org"],
                age_groups=["16-18"],
                processing_time=1.0
            )
        
        session = self.manager.get_session(self.session_id)
        
        # Should only keep the last 5 turns
        self.assertEqual(len(session.turns), 5)
        self.assertEqual(session.turns[0].user_message, "Message 2")  # Oldest kept
        self.assertEqual(session.turns[-1].user_message, "Message 6")  # Newest
    
    def test_context_summary_generation(self):
        """Test context summary generation for long conversations"""
        # Add multiple turns with different topics
        topics = [
            ("How do programs build confidence?", "confidence"),
            ("What about making friends?", "social"),
            ("Are there creative activities?", "creative"),
            ("How do you overcome challenges?", "challenges")
        ]
        
        for message, _ in topics:
            self.manager.add_turn(
                session_id=self.session_id,
                user_message=message,
                assistant_response="Response",
                evidence_count=1,
                organizations=["Test Org"],
                age_groups=["16-18"],
                processing_time=1.0
            )
        
        session = self.manager.get_session(self.session_id)
        
        # Should have generated context summary
        self.assertNotEqual(session.context_summary, "")
        self.assertIn("Recent discussion topics:", session.context_summary)
    
    def test_get_conversation_context_empty(self):
        """Test getting context for empty session"""
        context = self.manager.get_conversation_context("nonexistent_session")
        self.assertEqual(context, "")
    
    def test_get_conversation_context_with_turns(self):
        """Test getting conversation context with turns"""
        # Add some turns
        self.manager.add_turn(
            session_id=self.session_id,
            user_message="How do programs help?",
            assistant_response="Programs help by building confidence and social skills...",
            evidence_count=2,
            organizations=["YCUK"],
            age_groups=["16-18"],
            processing_time=1.5
        )
        
        self.manager.add_turn(
            session_id=self.session_id,
            user_message="What about creative activities?",
            assistant_response="Creative activities are important for engagement...",
            evidence_count=1,
            organizations=["Palace for Life"],
            age_groups=["13-15"],
            processing_time=1.2
        )
        
        context = self.manager.get_conversation_context(self.session_id, max_turns=2)
        
        self.assertIn("Recent conversation:", context)
        self.assertIn("How do programs help?", context)
        self.assertIn("What about creative activities?", context)
        self.assertIn("Programs help by building confidence", context)
    
    def test_get_session_stats(self):
        """Test getting session statistics"""
        # Add some turns
        for i in range(3):
            self.manager.add_turn(
                session_id=self.session_id,
                user_message=f"Message {i}",
                assistant_response=f"Response {i}",
                evidence_count=i + 1,
                organizations=[f"Org{i}"],
                age_groups=[f"Age{i}"],
                processing_time=1.0 + i * 0.5
            )
        
        stats = self.manager.get_session_stats(self.session_id)
        
        self.assertEqual(stats['session_id'], self.session_id)
        self.assertEqual(stats['turns_count'], 3)
        self.assertEqual(stats['total_evidence_used'], 6)  # 1 + 2 + 3
        self.assertEqual(stats['average_processing_time'], 1.5)  # (1.0 + 1.5 + 2.0) / 3
        self.assertEqual(len(stats['organizations_discussed']), 3)
        self.assertEqual(len(stats['age_groups_discussed']), 3)
    
    def test_get_session_stats_nonexistent(self):
        """Test getting stats for non-existent session"""
        stats = self.manager.get_session_stats("nonexistent_session")
        self.assertIn("error", stats)


class TestConversationalRAGAdapter(unittest.TestCase):
    """Test cases for ConversationalRAGAdapter"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock RAG engine
        self.mock_rag_engine = Mock()
        self.mock_rag_response = {
            'question': 'Test query',
            'answer': 'Test answer based on survey data',
            'source_documents': [{'text': 'Test doc', 'organization': 'Test Org'}],
            'evidence_count': 1,
            'organizations': ['Test Org'],
            'age_groups': ['16-18'],
            'genders': ['Male'],
            'processing_time': 1.5
        }
        self.mock_rag_engine.process_query.return_value = self.mock_rag_response
        
        # Create adapter
        self.adapter = ConversationalRAGAdapter(self.mock_rag_engine)
        self.session_id = "test_session"
    
    def test_initialization(self):
        """Test adapter initialization"""
        self.assertEqual(self.adapter.rag_engine, self.mock_rag_engine)
        self.assertIsInstance(self.adapter.conversation_manager, ServerlessConversationManager)
    
    def test_initialization_with_custom_manager(self):
        """Test adapter initialization with custom conversation manager"""
        custom_manager = ServerlessConversationManager(max_turns_per_session=20)
        adapter = ConversationalRAGAdapter(self.mock_rag_engine, custom_manager)
        
        self.assertEqual(adapter.conversation_manager, custom_manager)
        self.assertEqual(adapter.conversation_manager.max_turns_per_session, 20)
    
    def test_chat_first_message(self):
        """Test chat with first message (no context)"""
        message = "How do programs build confidence?"
        
        response = self.adapter.chat(message, self.session_id, include_context=False)
        
        # Verify RAG engine was called
        self.mock_rag_engine.process_query.assert_called_once_with(message)
        
        # Verify response structure
        self.assertEqual(response['session_id'], self.session_id)
        self.assertEqual(response['turn_number'], 1)
        self.assertFalse(response['conversation_context_used'])
        self.assertIn('total_processing_time', response)
        
        # Verify conversation metadata
        self.assertIn('conversation_metadata', response)
        self.assertFalse(response['conversation_metadata']['is_follow_up'])
        self.assertFalse(response['conversation_metadata']['context_used'])
        self.assertEqual(response['conversation_metadata']['session_length'], 1)
    
    def test_chat_with_context(self):
        """Test chat with conversation context"""
        # First message to establish context
        self.adapter.chat("How do programs help?", self.session_id)
        
        # Second message should use context
        message = "What about confidence building?"
        response = self.adapter.chat(message, self.session_id, include_context=True)
        
        # Should be called twice (first message + second message)
        self.assertEqual(self.mock_rag_engine.process_query.call_count, 2)
        
        # Second call should have enhanced query with context
        second_call_args = self.mock_rag_engine.process_query.call_args_list[1][0][0]
        self.assertIn("Previous conversation context:", second_call_args)
        self.assertIn("What about confidence building?", second_call_args)
        
        # Verify response indicates context was used
        self.assertTrue(response['conversation_context_used'])
        self.assertEqual(response['turn_number'], 2)
        self.assertTrue(response['conversation_metadata']['is_follow_up'])
    
    def test_chat_without_context(self):
        """Test chat without using conversation context"""
        # First message
        self.adapter.chat("How do programs help?", self.session_id)
        
        # Second message without context
        message = "What about confidence building?"
        response = self.adapter.chat(message, self.session_id, include_context=False)
        
        # Second call should not have enhanced query
        second_call_args = self.mock_rag_engine.process_query.call_args_list[1][0][0]
        self.assertEqual(second_call_args, message)
        
        # Verify response indicates no context was used
        self.assertFalse(response['conversation_context_used'])
        self.assertFalse(response['conversation_metadata']['context_used'])
    
    def test_chat_error_handling(self):
        """Test chat error handling"""
        # Mock RAG engine to raise exception
        self.mock_rag_engine.process_query.side_effect = Exception("RAG engine failed")
        
        message = "Test message"
        response = self.adapter.chat(message, self.session_id)
        
        # Should return error response
        self.assertIn('error', response)
        self.assertIn("encountered an error", response['answer'])
        self.assertEqual(response['evidence_count'], 0)
        self.assertEqual(response['session_id'], self.session_id)
    
    def test_get_conversation_history_existing(self):
        """Test getting conversation history for existing session"""
        # Add some conversation turns
        self.adapter.chat("First message", self.session_id)
        self.adapter.chat("Second message", self.session_id)
        
        history = self.adapter.get_conversation_history(self.session_id, max_turns=5)
        
        self.assertTrue(history['exists'])
        self.assertEqual(history['session_id'], self.session_id)
        self.assertEqual(len(history['turns']), 2)
        self.assertEqual(history['total_turns'], 2)
        self.assertIn('created_at', history)
        self.assertIn('last_activity', history)
    
    def test_get_conversation_history_nonexistent(self):
        """Test getting conversation history for non-existent session"""
        history = self.adapter.get_conversation_history("nonexistent_session")
        
        self.assertFalse(history['exists'])
        self.assertEqual(history['session_id'], "nonexistent_session")
        self.assertEqual(history['turns'], [])
    
    def test_get_conversation_history_with_limit(self):
        """Test getting conversation history with turn limit"""
        # Add multiple turns
        for i in range(5):
            self.adapter.chat(f"Message {i}", self.session_id)
        
        history = self.adapter.get_conversation_history(self.session_id, max_turns=3)
        
        # Should only return last 3 turns
        self.assertEqual(len(history['turns']), 3)
        self.assertEqual(history['total_turns'], 5)
        
        # Should be the most recent turns
        self.assertEqual(history['turns'][0]['user_message'], "Message 2")
        self.assertEqual(history['turns'][-1]['user_message'], "Message 4")
    
    def test_clear_session_existing(self):
        """Test clearing an existing session"""
        # Create session with some turns
        self.adapter.chat("Test message", self.session_id)
        
        # Verify session exists
        self.assertIsNotNone(self.adapter.conversation_manager.get_session(self.session_id))
        
        # Clear session
        result = self.adapter.clear_session(self.session_id)
        
        self.assertTrue(result)
        self.assertIsNone(self.adapter.conversation_manager.get_session(self.session_id))
    
    def test_clear_session_nonexistent(self):
        """Test clearing a non-existent session"""
        result = self.adapter.clear_session("nonexistent_session")
        self.assertFalse(result)
    
    def test_get_all_sessions_stats_empty(self):
        """Test getting stats when no sessions exist"""
        stats = self.adapter.get_all_sessions_stats()
        
        self.assertEqual(stats['active_sessions'], 0)
        self.assertEqual(stats['total_turns'], 0)
        self.assertEqual(stats['sessions'], [])
    
    def test_get_all_sessions_stats_with_sessions(self):
        """Test getting stats with active sessions"""
        # Create multiple sessions
        self.adapter.chat("Message 1", "session_1")
        self.adapter.chat("Message 2", "session_1")
        self.adapter.chat("Message 1", "session_2")
        
        stats = self.adapter.get_all_sessions_stats()
        
        self.assertEqual(stats['active_sessions'], 2)
        self.assertEqual(stats['total_turns'], 3)
        self.assertEqual(len(stats['sessions']), 2)
        
        # Check session details
        session_ids = [s['session_id'] for s in stats['sessions']]
        self.assertIn('session_1', session_ids)
        self.assertIn('session_2', session_ids)
    
    def test_enhance_query_with_context(self):
        """Test query enhancement with context"""
        message = "What about confidence?"
        context = "Previous conversation:\nUser: How do programs help?\nAssistant: Programs help by..."
        
        enhanced = self.adapter._enhance_query_with_context(message, context)
        
        self.assertIn("Previous conversation context:", enhanced)
        self.assertIn(context, enhanced)
        self.assertIn("What about confidence?", enhanced)
        self.assertIn("taking into account our previous discussion", enhanced)
    
    def test_enhance_query_no_context(self):
        """Test query enhancement without context"""
        message = "What about confidence?"
        context = ""
        
        enhanced = self.adapter._enhance_query_with_context(message, context)
        
        self.assertEqual(enhanced, message)
    
    def test_enhance_response_for_conversation(self):
        """Test response enhancement for conversational flow"""
        # Create a session with some history
        session = self.adapter.conversation_manager.create_session(self.session_id)
        context = "Previous discussion about programs"
        
        enhanced = self.adapter._enhance_response_for_conversation(
            self.mock_rag_response, session, context
        )
        
        self.assertIn('conversation_metadata', enhanced)
        metadata = enhanced['conversation_metadata']
        self.assertFalse(metadata['is_follow_up'])  # First turn
        self.assertTrue(metadata['context_used'])
        self.assertEqual(metadata['session_length'], 0)


class TestFactoryFunction(unittest.TestCase):
    """Test factory function"""
    
    def test_create_conversational_rag_default(self):
        """Test creating conversational RAG with default settings"""
        mock_engine = Mock()
        adapter = create_conversational_rag(mock_engine)
        
        self.assertIsInstance(adapter, ConversationalRAGAdapter)
        self.assertEqual(adapter.rag_engine, mock_engine)
        self.assertEqual(adapter.conversation_manager.max_turns_per_session, 10)
        self.assertEqual(adapter.conversation_manager.session_timeout_hours, 24)
    
    def test_create_conversational_rag_custom(self):
        """Test creating conversational RAG with custom settings"""
        mock_engine = Mock()
        adapter = create_conversational_rag(
            mock_engine, 
            max_turns=20, 
            session_timeout_hours=48
        )
        
        self.assertIsInstance(adapter, ConversationalRAGAdapter)
        self.assertEqual(adapter.conversation_manager.max_turns_per_session, 20)
        self.assertEqual(adapter.conversation_manager.session_timeout_hours, 48)


if __name__ == '__main__':
    unittest.main()