/**
 * useWebSocket.js
 *
 * 웹소켓 연결의 생성, 유지, 해제 및 메시지 수신을 중앙에서 관리하는 모듈.
 * 이 모듈은 메시지의 내용이 무엇인지는 관여하지 않고, 연결과 전달의 역할만 수행합니다.
 */
import { ref, readonly } from 'vue';

// 모듈 스코프에서 웹소켓 인스턴스와 연결 상태를 관리합니다.
const socket = ref(null);
const isConnected = ref(false);
// 외부에서 전달받을 메시지 처리 콜백 함수
let onMessageCallback = null;

export function useWebSocket() {

    /**
     * 웹소켓 서버에 연결을 시도합니다.
     * @param {string} url - 연결할 웹소켓 서버의 주소
     * @param {function} callback - 메시지 수신 시 실행할 콜백 함수
     */
    const connect = (url, callback) => {
        if (socket.value && isConnected.value) {
            console.log("[useWebSocket] WebSocket is already connected.");
            return;
        }
        
        onMessageCallback = callback;
        socket.value = new WebSocket(url);
        
        // 웹소켓 연결이 성공적으로 열렸을 때 자동으로 실행될 코드를 지정합니다.
        socket.value.onopen = () => {
            isConnected.value = true;
            console.log("[useWebSocket] WebSocket connected.");
        };

        // 서버로부터 메시지가 도착했을 때 자동으로 실행될 코드를 지정합니다. 
        // event.data에 서버가 보낸 메시지가 담겨 있습니다.
        socket.value.onmessage = (event) => {
            console.log("[useWebSocket] WebSocket message received.");
            if (onMessageCallback) {
                // 메시지가 오면, 등록된 콜백 함수를 호출하여 데이터 처리를 위임합니다.
                onMessageCallback(event.data);
            }
        };

        // 연결이 끊어졌을 때 자동으로 실행될 코드를 지정합니다.
        socket.value.onclose = () => {
            isConnected.value = false;
            console.log("[useWebSocket] WebSocket disconnected.");
            socket.value = null;
        };

        // 에러가 발생했을 때 자동으로 실행될 코드를 지정합니다.
        socket.value.onerror = (error) => {
            console.error("[useWebSocket] WebSocket error:", error);
        };
    };

    /**
     * 현재 활성화된 웹소켓 연결을 해제합니다.
     */
    const disconnect = () => {
        if (socket.value) {
            socket.value.close();
        }
    };

    return {
        isConnected: readonly(isConnected),
        connect,
        disconnect,
    };
}
