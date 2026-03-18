import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';
import axios from 'axios';
import { format } from 'date-fns';
import { LinearGradient } from 'expo-linear-gradient';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  code_executed?: string;
  code_result?: string;
}

export default function Index() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const scrollViewRef = useRef<ScrollView>(null);
  const userId = 'default_user';

  useEffect(() => {
    loadConversationHistory();
    requestAudioPermissions();
  }, []);

  const requestAudioPermissions = async () => {
    try {
      await Audio.requestPermissionsAsync();
    } catch (error) {
      console.error('Error requesting audio permissions:', error);
    }
  };

  const loadConversationHistory = async () => {
    try {
      const response = await axios.get(
        `${EXPO_PUBLIC_BACKEND_URL}/api/conversation/${userId}`
      );
      if (response.data.messages) {
        setMessages(response.data.messages);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/chat`, {
        message: text,
        user_id: userId,
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        code_executed: response.data.code_executed,
        code_result: response.data.code_result,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Auto-speak Luna's response
      if (response.data.response) {
        speakText(response.data.response);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      Alert.alert('Error', 'Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const speakText = (text: string) => {
    // Clean the text for speaking (remove code execution results)
    const cleanText = text.split('📊 Code Execution Result:')[0].trim();
    
    setIsSpeaking(true);
    Speech.speak(cleanText, {
      language: 'en-US',
      pitch: 1.0,
      rate: 0.9,
      onDone: () => setIsSpeaking(false),
      onStopped: () => setIsSpeaking(false),
      onError: () => setIsSpeaking(false),
    });
  };

  const stopSpeaking = () => {
    Speech.stop();
    setIsSpeaking(false);
  };

  const startRecording = async () => {
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );

      setRecording(recording);
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      Alert.alert('Error', 'Failed to start recording. Please check permissions.');
    }
  };

  const stopRecording = async () => {
    if (!recording) return;

    try {
      setIsRecording(false);
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);

      // Note: Voice-to-text would require additional API integration
      // For now, show a message that voice input was recorded
      Alert.alert(
        'Voice Input',
        'Voice-to-text feature requires additional setup. Please type your message for now.',
        [{ text: 'OK' }]
      );
    } catch (error) {
      console.error('Failed to stop recording:', error);
    }
  };

  const clearConversation = async () => {
    Alert.alert(
      'Clear Conversation',
      'Are you sure you want to clear all messages? Luna will forget this conversation.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await axios.delete(
                `${EXPO_PUBLIC_BACKEND_URL}/api/conversation/${userId}`
              );
              setMessages([]);
              Alert.alert('Cleared', 'Conversation history has been cleared.');
            } catch (error) {
              console.error('Error clearing conversation:', error);
              Alert.alert('Error', 'Failed to clear conversation.');
            }
          },
        },
      ]
    );
  };

  const renderMessage = (message: Message, index: number) => {
    const isUser = message.role === 'user';
    const time = format(new Date(message.timestamp), 'h:mm a');

    return (
      <View
        key={index}
        style={[
          styles.messageContainer,
          isUser ? styles.userMessageContainer : styles.assistantMessageContainer,
        ]}
      >
        {!isUser && (
          <View style={styles.avatarContainer}>
            <LinearGradient
              colors={['#667eea', '#764ba2']}
              style={styles.avatar}
            >
              <Ionicons name="moon" size={20} color="#fff" />
            </LinearGradient>
          </View>
        )}
        <View
          style={[
            styles.messageBubble,
            isUser ? styles.userBubble : styles.assistantBubble,
          ]}
        >
          <Text style={[styles.messageText, isUser && styles.userMessageText]}>
            {message.content}
          </Text>
          {message.code_executed && (
            <View style={styles.codeContainer}>
              <Text style={styles.codeLabel}>Code Executed:</Text>
              <Text style={styles.codeText}>{message.code_executed}</Text>
            </View>
          )}
          <Text style={[styles.timeText, isUser && styles.userTimeText]}>
            {time}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <LinearGradient
        colors={['#667eea', '#764ba2']}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View style={styles.headerLeft}>
            <View style={styles.headerAvatar}>
              <Ionicons name="moon" size={24} color="#fff" />
            </View>
            <View>
              <Text style={styles.headerTitle}>Luna</Text>
              <Text style={styles.headerSubtitle}>
                {isSpeaking ? 'Speaking...' : 'Your AI Companion'}
              </Text>
            </View>
          </View>
          <TouchableOpacity onPress={clearConversation} style={styles.clearButton}>
            <Ionicons name="trash-outline" size={24} color="#fff" />
          </TouchableOpacity>
        </View>
      </LinearGradient>

      {/* Messages */}
      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
        onContentSizeChange={() =>
          scrollViewRef.current?.scrollToEnd({ animated: true })
        }
      >
        {messages.length === 0 ? (
          <View style={styles.emptyContainer}>
            <LinearGradient
              colors={['#667eea', '#764ba2']}
              style={styles.emptyAvatar}
            >
              <Ionicons name="moon" size={48} color="#fff" />
            </LinearGradient>
            <Text style={styles.emptyTitle}>Hi! I'm Luna 🌙</Text>
            <Text style={styles.emptyText}>
              Your intelligent AI companion who's always here for you.
            </Text>
            <Text style={styles.emptyText}>
              I can chat, write code, and help with anything you need.
            </Text>
            <Text style={styles.emptySubtext}>
              Tap the microphone to speak or type a message below
            </Text>
          </View>
        ) : (
          messages.map((message, index) => renderMessage(message, index))
        )}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#667eea" />
            <Text style={styles.loadingText}>Luna is thinking...</Text>
          </View>
        )}
      </ScrollView>

      {/* Input Area */}
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        <View style={styles.inputContainer}>
          {isSpeaking && (
            <TouchableOpacity
              style={styles.stopSpeakingButton}
              onPress={stopSpeaking}
            >
              <Ionicons name="volume-mute" size={20} color="#fff" />
              <Text style={styles.stopSpeakingText}>Stop Speaking</Text>
            </TouchableOpacity>
          )}
          <View style={styles.inputRow}>
            <TouchableOpacity
              style={[
                styles.voiceButton,
                isRecording && styles.voiceButtonActive,
              ]}
              onPressIn={startRecording}
              onPressOut={stopRecording}
            >
              <Ionicons
                name={isRecording ? 'mic' : 'mic-outline'}
                size={24}
                color={isRecording ? '#fff' : '#667eea'}
              />
            </TouchableOpacity>

            <TextInput
              style={styles.input}
              placeholder="Message Luna..."
              placeholderTextColor="#999"
              value={inputText}
              onChangeText={setInputText}
              multiline
              maxLength={1000}
              editable={!isLoading}
              onSubmitEditing={() => sendMessage(inputText)}
            />

            <TouchableOpacity
              style={[
                styles.sendButton,
                (!inputText.trim() || isLoading) && styles.sendButtonDisabled,
              ]}
              onPress={() => sendMessage(inputText)}
              disabled={!inputText.trim() || isLoading}
            >
              <LinearGradient
                colors={
                  inputText.trim() && !isLoading
                    ? ['#667eea', '#764ba2']
                    : ['#ccc', '#999']
                }
                style={styles.sendButtonGradient}
              >
                <Ionicons name="send" size={20} color="#fff" />
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.3)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  clearButton: {
    padding: 8,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 8,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 60,
  },
  emptyAvatar: {
    width: 96,
    height: 96,
    borderRadius: 48,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  emptyTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 8,
    paddingHorizontal: 32,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    marginTop: 16,
    paddingHorizontal: 32,
  },
  messageContainer: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  userMessageContainer: {
    justifyContent: 'flex-end',
  },
  assistantMessageContainer: {
    justifyContent: 'flex-start',
  },
  avatarContainer: {
    marginRight: 8,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  messageBubble: {
    maxWidth: '75%',
    padding: 12,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: '#667eea',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#fff',
    borderBottomLeftRadius: 4,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  messageText: {
    fontSize: 16,
    color: '#333',
    lineHeight: 22,
  },
  userMessageText: {
    color: '#fff',
  },
  timeText: {
    fontSize: 11,
    color: '#999',
    marginTop: 6,
  },
  userTimeText: {
    color: 'rgba(255,255,255,0.7)',
  },
  codeContainer: {
    marginTop: 8,
    padding: 8,
    backgroundColor: 'rgba(0,0,0,0.05)',
    borderRadius: 8,
  },
  codeLabel: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 4,
  },
  codeText: {
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    color: '#333',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#667eea',
    fontStyle: 'italic',
  },
  inputContainer: {
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    paddingHorizontal: 16,
    paddingVertical: 12,
    paddingBottom: Platform.OS === 'ios' ? 32 : 12,
  },
  stopSpeakingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#667eea',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    marginBottom: 12,
  },
  stopSpeakingText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  voiceButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#f0f0f0',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  voiceButtonActive: {
    backgroundColor: '#667eea',
  },
  input: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    maxHeight: 100,
    color: '#333',
  },
  sendButton: {
    marginLeft: 8,
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  sendButtonGradient: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
