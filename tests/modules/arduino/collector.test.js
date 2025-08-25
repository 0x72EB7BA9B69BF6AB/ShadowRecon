/**
 * Arduino Collector Tests
 * Test suite for Arduino data collection functionality
 */

const { ArduinoCollector } = require('../../../src/modules/arduino/collector');

// Mock the statistics module
jest.mock('../../../src/core/statistics', () => ({
    stats: {
        addArduino: jest.fn()
    }
}));

describe('ArduinoCollector', () => {
    let collector;

    beforeEach(() => {
        collector = new ArduinoCollector();
    });

    afterEach(async () => {
        if (collector) {
            await collector.cleanup();
        }
    });

    describe('Initialization', () => {
        test('should initialize successfully', async () => {
            const result = await collector.initialize();
            expect(result).toBe(true);
            expect(collector.spoofer).toBeDefined();
        });

        test('should handle initialization failure gracefully', async () => {
            // Mock spoofer initialization failure
            const mockSpoofer = {
                initialize: jest.fn().mockResolvedValue(false)
            };
            collector.spoofer = mockSpoofer;

            const result = await collector.initialize();
            expect(result).toBe(true); // Should still return true, just with warning
        });
    });

    describe('Data Collection', () => {
        test('should collect data successfully with mock spoofer', async () => {
            // Setup mock spoofer
            const mockDevices = [
                { id: 'device1', name: 'Arduino Uno', type: 'arduino' },
                { id: 'device2', name: 'USB Host Shield', type: 'usb_host_shield' }
            ];

            const mockSpoofer = {
                enumerateDevices: jest.fn().mockResolvedValue(mockDevices),
                spoofDevice: jest.fn().mockResolvedValue(true),
                getSpoofingStatus: jest.fn().mockReturnValue({
                    totalDevices: 2,
                    spoofedDevices: 2,
                    hostShieldHidden: true,
                    mouseControllerReady: true,
                    platform: 'test'
                }),
                moveMouse: jest.fn().mockResolvedValue(true),
                clickMouse: jest.fn().mockResolvedValue(true)
            };

            collector.spoofer = mockSpoofer;

            const result = await collector.collect();

            expect(result.success).toBe(true);
            expect(result.devicesFound).toBe(2);
            expect(result.devicesSpoofed).toBe(2);
            expect(result.hostShieldHidden).toBe(true);
            expect(result.mouseControllerReady).toBe(true);
        });

        test('should handle collection failure when spoofer not initialized', async () => {
            collector.spoofer = null;

            const result = await collector.collect();

            expect(result.success).toBe(false);
            expect(result.devicesFound).toBe(0);
            expect(result.errors).toContain('[SPOOFER_NOT_READY] Arduino spoofer not initialized');
        });

        test('should handle spoofing errors gracefully', async () => {
            const mockDevices = [
                { id: 'device1', name: 'Arduino Uno', type: 'arduino' }
            ];

            const mockSpoofer = {
                enumerateDevices: jest.fn().mockResolvedValue(mockDevices),
                spoofDevice: jest.fn().mockRejectedValue(new Error('Spoofing failed')),
                getSpoofingStatus: jest.fn().mockReturnValue({
                    totalDevices: 1,
                    spoofedDevices: 0,
                    hostShieldHidden: false,
                    mouseControllerReady: false
                })
            };

            collector.spoofer = mockSpoofer;

            const result = await collector.collect();

            expect(result.success).toBe(true);
            expect(result.devicesFound).toBe(1);
            expect(result.devicesSpoofed).toBe(0);
        });
    });

    describe('Auto Spoofing', () => {
        test('should prioritize Arduino and USB Host Shield devices', async () => {
            const devices = [
                { id: 'device1', name: 'Arduino Uno', type: 'arduino' },
                { id: 'device2', name: 'Generic USB', type: 'usb_device' },
                { id: 'device3', name: 'USB Host Shield', type: 'usb_host_shield' },
                { id: 'device4', name: 'Arduino HID', type: 'hid_device', name: 'Arduino Keyboard' }
            ];

            const mockSpoofer = {
                spoofDevice: jest.fn().mockResolvedValue(true)
            };
            collector.spoofer = mockSpoofer;

            const result = await collector.performAutoSpoofing(devices);

            // Should spoof Arduino, USB Host Shield, and Arduino HID
            expect(result.spoofedCount).toBe(3);
            expect(mockSpoofer.spoofDevice).toHaveBeenCalledTimes(3);
        });
    });

    describe('Report Generation', () => {
        test('should generate devices report', () => {
            collector.collectedData.devices = [
                { id: 'device1', name: 'Arduino Uno', type: 'arduino', platform: 'test' }
            ];

            const report = collector.generateDevicesReport();

            expect(report).toContain('=== ARDUINO AND USB DEVICES (1 entries) ===');
            expect(report).toContain('Arduino Uno');
            expect(report).toContain('device1');
            expect(report).toContain('Type: arduino');
        });

        test('should generate spoofing status report', () => {
            collector.collectedData.spoofingStatus = {
                totalDevices: 2,
                spoofedDevices: 1,
                hostShieldHidden: true,
                mouseControllerReady: false,
                platform: 'test',
                spoofedDeviceDetails: [
                    {
                        originalId: 'device1',
                        spoofedId: 'spoofed1',
                        spoofedName: 'Generic USB Device',
                        spoofingDuration: 5000
                    }
                ]
            };

            const report = collector.generateSpoofingReport();

            expect(report).toContain('=== ARDUINO SPOOFING STATUS ===');
            expect(report).toContain('Total Devices Found: 2');
            expect(report).toContain('Devices Spoofed: 1');
            expect(report).toContain('USB Host Shield Hidden: Yes');
            expect(report).toContain('=== SPOOFED DEVICES DETAILS ===');
        });

        test('should generate operation logs report', () => {
            collector.collectedData.operationLogs = [
                {
                    timestamp: '2023-01-01T00:00:00.000Z',
                    operation: 'spoof_device',
                    data: {
                        success: true,
                        deviceId: 'device1',
                        deviceName: 'Arduino Uno'
                    }
                }
            ];

            const report = collector.generateOperationLogsReport();

            expect(report).toContain('=== ARDUINO OPERATION LOGS (1 entries) ===');
            expect(report).toContain('Operation: spoof_device');
            expect(report).toContain('Success: Yes');
            expect(report).toContain('Device ID: device1');
        });
    });

    describe('Data Summary', () => {
        test('should return correct data summary', () => {
            collector.collectedData = {
                devices: [{ id: 'device1' }, { id: 'device2' }],
                spoofingStatus: {
                    spoofedDevices: 1,
                    hostShieldHidden: true,
                    mouseControllerReady: false
                },
                operationLogs: [{ operation: 'test' }]
            };

            const summary = collector.getDataSummary();

            expect(summary.devicesCount).toBe(2);
            expect(summary.spoofedDevicesCount).toBe(1);
            expect(summary.hostShieldHidden).toBe(true);
            expect(summary.mouseControllerReady).toBe(false);
            expect(summary.operationLogsCount).toBe(1);
        });
    });

    describe('Cleanup', () => {
        test('should cleanup successfully', async () => {
            const mockSpoofer = {
                cleanup: jest.fn().mockResolvedValue()
            };
            collector.spoofer = mockSpoofer;

            await collector.cleanup();

            expect(mockSpoofer.cleanup).toHaveBeenCalled();
            expect(collector.collectedData.devices).toHaveLength(0);
            expect(collector.collectedData.operationLogs).toHaveLength(0);
        });

        test('should handle cleanup errors gracefully', async () => {
            const mockSpoofer = {
                cleanup: jest.fn().mockRejectedValue(new Error('Cleanup failed'))
            };
            collector.spoofer = mockSpoofer;

            // Should not throw
            await expect(collector.cleanup()).resolves.not.toThrow();
        });
    });
});