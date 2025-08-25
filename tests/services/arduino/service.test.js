/**
 * Arduino Service Tests
 * Test suite for Arduino service functionality
 */

const { ArduinoService } = require('../../../src/services/arduino/service');

describe('ArduinoService', () => {
    let service;

    beforeEach(() => {
        service = new ArduinoService();
    });

    afterEach(async () => {
        if (service) {
            await service.cleanup();
        }
    });

    describe('Initialization', () => {
        test('should initialize successfully', async () => {
            await service.initialize();
            
            expect(service.collector).toBeDefined();
            expect(service.initialized).toBe(true);
        });

        test('should handle initialization failure gracefully', async () => {
            // Mock collector that fails to initialize
            const mockCollector = {
                initialize: jest.fn().mockResolvedValue(false)
            };
            
            service.collector = mockCollector;
            await service.initialize();
            
            expect(service.initialized).toBe(false);
        });
    });

    describe('Data Collection', () => {
        test('should collect data when initialized', async () => {
            // Setup mock collector
            const mockResults = {
                success: true,
                devicesFound: 2,
                devicesSpoofed: 1,
                hostShieldHidden: true,
                mouseControllerReady: false,
                collectionDuration: 1000
            };

            const mockCollector = {
                initialize: jest.fn().mockResolvedValue(true),
                collect: jest.fn().mockResolvedValue(mockResults),
                getDataSummary: jest.fn().mockReturnValue({
                    devicesCount: 2,
                    spoofedDevicesCount: 1,
                    hostShieldHidden: true,
                    mouseControllerReady: false,
                    operationLogsCount: 3
                })
            };

            service.collector = mockCollector;
            service.initialized = true;

            const result = await service.collect();

            expect(result.success).toBe(true);
            expect(result.devicesFound).toBe(2);
            expect(result.devicesSpoofed).toBe(1);
            expect(result.hostShieldHidden).toBe(true);
            expect(mockCollector.collect).toHaveBeenCalled();
        });

        test('should handle collection when not initialized', async () => {
            service.initialized = false;
            service.collector = null;

            const result = await service.collect();

            expect(result.success).toBe(false);
            expect(result.message).toBe('Service not initialized');
            expect(result.devicesFound).toBe(0);
            expect(result.devicesSpoofed).toBe(0);
        });

        test('should handle collection errors', async () => {
            const mockCollector = {
                collect: jest.fn().mockRejectedValue(new Error('Collection failed'))
            };

            service.collector = mockCollector;
            service.initialized = true;

            const result = await service.collect();

            expect(result.success).toBe(false);
            expect(result.message).toBe('Collection failed');
        });
    });

    describe('Service Status', () => {
        test('should return correct availability status', () => {
            // Not available when not initialized
            expect(service.isAvailable()).toBe(false);

            // Available when initialized with collector
            service.initialized = true;
            service.collector = {};
            expect(service.isAvailable()).toBe(true);

            // Not available when initialized but no collector
            service.collector = null;
            expect(service.isAvailable()).toBe(false);
        });

        test('should return correct health status', () => {
            const mockCollector = {
                getDataSummary: jest.fn().mockReturnValue({
                    devicesCount: 2,
                    spoofedDevicesCount: 1,
                    hostShieldHidden: true,
                    mouseControllerReady: false,
                    operationLogsCount: 3
                })
            };

            service.collector = mockCollector;
            service.initialized = true;
            service.collectionResults = {
                success: true,
                devicesFound: 2
            };

            const health = service.getHealthStatus();

            expect(health.healthy).toBe(true);
            expect(health.initialized).toBe(true);
            expect(health.collectorReady).toBe(true);
            expect(health.dataCollected).toBe(true);
            expect(health.devicesFound).toBe(2);
        });

        test('should return results summary', () => {
            const mockCollector = {
                getDataSummary: jest.fn().mockReturnValue({
                    devicesCount: 3,
                    spoofedDevicesCount: 2,
                    hostShieldHidden: false,
                    mouseControllerReady: true,
                    operationLogsCount: 5
                })
            };

            service.collector = mockCollector;
            service.collectionResults = {
                success: true,
                devicesFound: 3,
                devicesSpoofed: 2,
                hostShieldHidden: false,
                mouseControllerReady: true
            };

            const results = service.getResults();

            expect(results.dataCollected).toBe(true);
            expect(results.devicesFound).toBe(3);
            expect(results.devicesSpoofed).toBe(2);
            expect(results.devicesCount).toBe(3);
            expect(results.spoofedDevicesCount).toBe(2);
        });

        test('should handle missing results gracefully', () => {
            service.collectionResults = null;
            service.collector = null;

            const results = service.getResults();

            expect(results.dataCollected).toBe(false);
            expect(results.devicesFound).toBe(0);
            expect(results.devicesSpoofed).toBe(0);
        });
    });

    describe('Service Lifecycle', () => {
        test('should restart successfully', async () => {
            const initializeSpy = jest.spyOn(service, 'initialize').mockResolvedValue();
            const cleanupSpy = jest.spyOn(service, 'cleanup').mockResolvedValue();

            const result = await service.restart();

            expect(cleanupSpy).toHaveBeenCalled();
            expect(initializeSpy).toHaveBeenCalled();
            expect(result).toBe(service.initialized);
        });

        test('should handle restart errors', async () => {
            jest.spyOn(service, 'cleanup').mockRejectedValue(new Error('Cleanup failed'));

            const result = await service.restart();

            expect(result).toBe(false);
        });

        test('should cleanup successfully', async () => {
            const mockCollector = {
                cleanup: jest.fn().mockResolvedValue()
            };

            service.collector = mockCollector;
            service.initialized = true;
            service.collectionResults = { success: true };

            await service.cleanup();

            expect(mockCollector.cleanup).toHaveBeenCalled();
            expect(service.collector).toBeNull();
            expect(service.initialized).toBe(false);
            expect(service.collectionResults).toBeNull();
        });

        test('should handle cleanup errors gracefully', async () => {
            const mockCollector = {
                cleanup: jest.fn().mockRejectedValue(new Error('Cleanup failed'))
            };

            service.collector = mockCollector;

            // Should not throw
            await expect(service.cleanup()).resolves.not.toThrow();
            expect(service.collector).toBeNull();
            expect(service.initialized).toBe(false);
        });
    });
});