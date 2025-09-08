/**
 * useWebSocket.js (Connection Manager)
 *
 * 여러 개의 명명된 웹소켓 연결을 동시에 생성, 유지, 해제하는 '커넥션 매니저' 모듈.
 * 각 연결은 고유한 키(예: version_id)로 식별됩니다.
 */
import { ref, readonly } from 'vue';

// 모듈 스코프에서 모든 웹소켓 연결 인스턴스를 관리합니다.
// { key: { socket: WebSocket, isConnected: boolean, callback: function }, ... }
const connections = ref({});

export function useWebSocket() {

    /**
     * 특정 키로 식별되는 웹소켓 서버에 연결을 시도합니다.
     * @param {string | number} key - 이 연결을 식별할 고유 키 (예: versionId)
     * @param {string} url - 연결할 웹소켓 서버의 주소
     * @param {function} callback - 메시지 수신 시 실행할 콜백 함수
     */
    const connect = (key, url, callback) => new Promise((resolve, reject) => {
        if (connections.value[key]?.isConnected) {
            // console.log(`[WS Manager] Connection for key '${key}' is already active.`);
            resolve(); // 이미 연결되어 있으면 성공으로 간주
            return;
        }

        const socket = new WebSocket(url);

        connections.value[key] = {
            socket: socket,
            isConnected: false,
            callback: callback,
        };

        socket.onopen = () => {
            const conn = connections.value[key];
            if (conn) conn.isConnected = true;
            // console.log(`[WS Manager] Connected with key '${key}'.`);
            resolve(); // 연결 성공
        };

        socket.onmessage = (event) => {
            const conn = connections.value[key];
            if (conn?.callback) conn.callback(event.data);
        };

        socket.onclose = () => {
            // console.log(`[WS Manager] Disconnected from key '${key}'.`);
            if (connections.value[key]) {
                delete connections.value[key];
            }
        };

        socket.onerror = (error) => {
            console.error(`[WS Manager] Error on key '${key}':`, error);
            delete connections.value[key];
            reject(error); // 연결 실패
        };
    });

    /**
     * 특정 키의 웹소켓 연결을 해제합니다.
     * @param {string | number} key - 해제할 연결의 고유 키
     */
    const disconnect = (key) => {
        const conn = connections.value[key];
        if (conn && conn.socket) {
            conn.socket.close();
            // onclose 이벤트 핸들러에서 connections 객체 정리가 처리됩니다.
        }
    };

    /**
     * 모든 활성 웹소켓 연결을 해제합니다. (예: 로그아웃 시)
     */
    const disconnectAll = () => {
        // console.log("[WS Manager] Disconnecting all connections.");
        for (const key in connections.value) {
            disconnect(key);
        }
    };
    
    /**
     * 특정 키의 연결 상태를 확인하는 헬퍼 함수
     * @param {string | number} key 
     * @returns {boolean}
     */
    const isConnected = (key) => {
        return !!(connections.value[key] && connections.value[key].isConnected);
    };

    return {
        connections: readonly(connections),
        connect,
        disconnect,
        disconnectAll,
        isConnected,
    };
}
