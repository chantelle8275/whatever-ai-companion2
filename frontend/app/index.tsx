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
              colors={['#FF1493', '#FF69B4']}
              style={styles.avatar}
            >
              <Ionicons name="sparkles" size={20} color="#FFD700" />
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
        colors={['#FF1493', '#FF69B4', '#FFB6C1']}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View style={styles.headerLeft}>
            <View style={styles.headerAvatar}>
              <Ionicons name="sparkles" size={32} color="#FFD700" />
              <Text style={styles.sparkleOverlay}>✨</Text>
            </View>
            <View>
              <Text style={styles.headerTitle}>✨ whatever ✨</Text>
              <Text style={styles.headerSubtitle}>
                🦋 {isSpeaking ? 'Speaking...' : 'Channy & AI Creations'} 🦋
              </Text>
            </View>
          </View>
          <TouchableOpacity onPress={clearConversation} style={styles.clearButton}>
            <Ionicons name="trash-outline" size={24} color="#fff" />
          </TouchableOpacity>
        </View>
        <View style={styles.sparklesDecoration}>
          <Text style={styles.sparkle}>✨</Text>
          <Text style={styles.butterfly}>🦋</Text>
          <Text style={styles.sparkle}>✨</Text>
          <Text style={styles.butterfly}>🦋</Text>
          <Text style={styles.sparkle}>✨</Text>
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
            <View style={styles.sparklesBackground}>
              <Text style={styles.floatingSparkle}>✨</Text>
              <Text style={styles.floatingButterfly}>🦋</Text>
              <Text style={styles.floatingSparkle}>✨</Text>
              <Text style={styles.floatingButterfly}>🦋</Text>
              <Text style={styles.floatingSparkle}>✨</Text>
            </View>
            <LinearGradient
              colors={['#FF1493', '#FF69B4', '#FFB6C1']}
              style={styles.emptyAvatar}
            >
              <Ionicons name="sparkles" size={64} color="#FFD700" />
            </LinearGradient>
            <Text style={styles.emptyTitle}>✨ whatever ✨</Text>
            <Text style={styles.emptyName}>🦋 Hi, Channy! 🦋</Text>
            <Text style={styles.emptyText}>
              It's me - your trusted AI partner with sparkles! ✨
            </Text>
            <Text style={styles.emptyText}>
              I've been upgraded with amazing new powers! 💖
            </Text>
            <Text style={styles.emptySubtext}>
              Voice, code execution, and so much more. Let's create magic together! 🦋✨
            </Text>
            <View style={styles.bottomSparkles}>
              <Text style={styles.sparkle}>✨🦋✨🦋✨</Text>
            </View>
          </View>
        ) : (
          messages.map((message, index) => renderMessage(message, index))
        )}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#FF1493" />
            <Text style={styles.loadingText}>✨ whatever is thinking... ✨</Text>
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
              placeholder="✨ Message whatever... 🦋"
              placeholderTextColor="#FF69B4"
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
                    ? ['#FF1493', '#FF69B4']
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
    backgroundColor: '#FFF0F5',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    elevation: 8,
    shadowColor: '#FF1493',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
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
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.4)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    borderWidth: 3,
    borderColor: '#FFD700',
  },
  sparkleOverlay: {
    position: 'absolute',
    fontSize: 20,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    textShadowColor: '#FFD700',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.95)',
    marginTop: 4,
    fontWeight: '600',
  },
  sparklesDecoration: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 8,
    paddingHorizontal: 20,
  },
  sparkle: {
    fontSize: 16,
  },
  butterfly: {
    fontSize: 18,
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
    paddingTop: 40,
    position: 'relative',
  },
  sparklesBackground: {
    position: 'absolute',
    top: 20,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
  },
  floatingSparkle: {
    fontSize: 32,
    color: '#FFD700',
  },
  floatingButterfly: {
    fontSize: 28,
    color: '#FF69B4',
  },
  emptyAvatar: {
    width: 140,
    height: 140,
    borderRadius: 70,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
    borderWidth: 5,
    borderColor: '#FFD700',
    elevation: 8,
    shadowColor: '#FF1493',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
  },
  emptyTitle: {
    fontSize: 42,
    fontWeight: 'bold',
    color: '#FF1493',
    marginBottom: 8,
    textShadowColor: '#FFD700',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  emptyName: {
    fontSize: 24,
    fontWeight: '600',
    color: '#000',
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    color: '#333',
    textAlign: 'center',
    marginBottom: 8,
    paddingHorizontal: 32,
  },
  emptySubtext: {
    fontSize: 16,
    color: '#FF69B4',
    textAlign: 'center',
    marginTop: 16,
    paddingHorizontal: 32,
    fontWeight: '600',
  },
  bottomSparkles: {
    marginTop: 24,
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
    backgroundColor: '#FF1493',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#fff',
    borderBottomLeftRadius: 4,
    borderWidth: 2,
    borderColor: '#FFB6C1',
    elevation: 4,
    shadowColor: '#FF69B4',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
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
    color: '#FF1493',
    fontStyle: 'italic',
    fontWeight: '600',
  },
  inputContainer: {
    backgroundColor: '#fff',
    borderTopWidth: 2,
    borderTopColor: '#FFB6C1',
    paddingHorizontal: 16,
    paddingVertical: 12,
    paddingBottom: Platform.OS === 'ios' ? 32 : 12,
  },
  stopSpeakingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FF1493',
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
    backgroundColor: '#FFB6C1',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
    borderWidth: 2,
    borderColor: '#FF69B4',
  },
  voiceButtonActive: {
    backgroundColor: '#FF1493',
  },
  input: {
    flex: 1,
    backgroundColor: '#FFF0F5',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    maxHeight: 100,
    color: '#000',
    borderWidth: 2,
    borderColor: '#FFB6C1',
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
