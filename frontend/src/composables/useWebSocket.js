// frontend/src/composables/useWebSocket.js
import { ref, onUnmounted } from 'vue';
import { API_BASE_URL } from '../api'; // API_BASE_URL 임포트

export default function useWebSocket() {
  const ws = ref(null);
  const receivedMessage = ref(null);
  const isConnected = ref(false);

  const reconnectAttempts = ref(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 2000; // 2초

  const connectWebSocket = (versionId, userId) => {
    if (ws.value && isConnected.value) {
      console.warn('WebSocket is already connected.');
      return;
    }

    // WebSocket URL은 백엔드 API URL과 동일한 호스트를 사용하고, 포트는 웹소켓 포트(예: 8001)를 사용합니다。
    // 프로토콜은 ws:// 또는 wss:// (HTTPS의 경우)를 사용합니다。
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = API_BASE_URL.replace(/^(http|https):/, protocol); // API_BASE_URL 사용
    const websocketUrl = `${host}/ws/${versionId}`;

    console.log(`Attempting to connect WebSocket to: ${websocketUrl}`);
    ws.value = new WebSocket(websocketUrl);

    ws.value.onopen = () => {
      isConnected.value = true;
      console.log('WebSocket connected successfully.');
      // 연결 시 사용자 ID를 서버에 전송 (선택 사항, 서버에서 필요하다면)
      // ws.value.send(JSON.stringify({ type: 'user_id', userId: userId }));
    };

    ws.value.onmessage = (event) => {
      console.log('WebSocket message received:', event.data);
      receivedMessage.value = JSON.parse(event.data);
    };

    ws.value.onclose = (event) => {
      isConnected.value = false;
      console.log('WebSocket disconnected:', event.code, event.reason);
      
      if (reconnectAttempts.value < maxReconnectAttempts) {
        reconnectAttempts.value++;
        console.log(`Attempting to reconnect WebSocket (attempt ${reconnectAttempts.value}/${maxReconnectAttempts})...`);
        setTimeout(() => {
          // 기존 ws 인스턴스를 null로 설정하여 새 연결을 강제
          ws.value = null;
          connectWebSocket(versionId, userId);
        }, reconnectDelay);
      } else {
        console.error('Max WebSocket reconnect attempts reached. Please refresh the page.');
        reconnectAttempts.value = 0; // 재연결 시도 횟수 초기화 (수동 새로고침 시 다시 시도 가능하도록)
      }
    };

    ws.value.onerror = (error) => {
      console.error('WebSocket error:', error);
      isConnected.value = false;
    };
  };

  const sendMessage = (message) => {
    if (ws.value && isConnected.value) {
      ws.value.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  };

  const disconnectWebSocket = () => {
    if (ws.value && isConnected.value) {
      ws.value.close();
      ws.value = null;
      isConnected.value = false;
      console.log('WebSocket explicitly disconnected.');
    }
  };

  // 컴포넌트 언마운트 시 웹소켓 연결 해제
  onUnmounted(() => {
    disconnectWebSocket();
  });

  return {
    ws,
    receivedMessage,
    isConnected,
    connectWebSocket,
    sendMessage,
    disconnectWebSocket,
  };
}
