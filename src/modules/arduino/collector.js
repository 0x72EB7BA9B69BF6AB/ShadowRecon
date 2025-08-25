/**
 * Arduino Data Collector Module
 * Collects Arduino device information and manages spoofing operations
 */

const { logger } = require('../../core/logger');
const { ErrorHandler, ModuleError } = require('../../core/errors');
const { ArduinoSpoofer } = require('./spoofer');
const { fileManager } = require('../../core/fileManager');
const { stats } = require('../../core/statistics');

class ArduinoCollector {
    constructor() {
        this.spoofer = null;
        this.collectedData = {
            devices: [],
            spoofingStatus: {},
            mouseControllerInfo: {},
            operationLogs: []
        };
    }

    /**
     * Initialize Arduino collector
     * @returns {Promise<boolean>} True if initialization successful
     */
    async initialize() {
        try {
            logger.info('Initializing Arduino collector module');

            this.spoofer = new ArduinoSpoofer();
            const initSuccess = await this.spoofer.initialize();

            if (!initSuccess) {
                logger.warn('Arduino spoofer initialization failed, continuing without spoofing capabilities');
            }

            logger.info('Arduino collector module initialized', {
                spooferReady: initSuccess
            });

            return true;
        } catch (error) {
            logger.error('Arduino collector initialization failed:', error.message);
            ErrorHandler.handle(error, 'ArduinoCollector.initialize');
            return false;
        }
    }

    /**
     * Collect Arduino device data and perform spoofing operations
     * @returns {Promise<Object>} Collection results
     */
    async collect() {
        try {
            logger.info('Starting Arduino data collection and spoofing operations');

            const startTime = Date.now();
            const results = {
                success: false,
                devicesFound: 0,
                devicesSpoofed: 0,
                hostShieldHidden: false,
                mouseControllerReady: false,
                collectionDuration: 0,
                errors: []
            };

            if (!this.spoofer) {
                throw new ModuleError('Arduino spoofer not initialized', 'SPOOFER_NOT_READY');
            }

            // Enumerate devices
            const devices = await this.spoofer.enumerateDevices();
            this.collectedData.devices = devices;
            results.devicesFound = devices.length;

            logger.info(`Found ${devices.length} Arduino/USB devices`);

            // Auto-spoof USB Host Shields and Arduino devices
            const autoSpoofResults = await this.performAutoSpoofing(devices);
            results.devicesSpoofed = autoSpoofResults.spoofedCount;

            // Get spoofing status
            const spoofingStatus = this.spoofer.getSpoofingStatus();
            this.collectedData.spoofingStatus = spoofingStatus;
            results.hostShieldHidden = spoofingStatus.hostShieldHidden;
            results.mouseControllerReady = spoofingStatus.mouseControllerReady;

            // Save collection data
            await this.saveCollectionData();

            // Demo mouse control if available
            if (spoofingStatus.mouseControllerReady) {
                await this.demonstrateMouseControl();
            }

            // Update global statistics
            stats.addArduino(results);

            results.success = true;
            results.collectionDuration = Date.now() - startTime;

            logger.info('Arduino data collection completed successfully', {
                devicesFound: results.devicesFound,
                devicesSpoofed: results.devicesSpoofed,
                hostShieldHidden: results.hostShieldHidden,
                mouseControllerReady: results.mouseControllerReady,
                duration: `${results.collectionDuration}ms`
            });

            return results;
        } catch (error) {
            logger.error('Arduino data collection failed:', error.message);
            ErrorHandler.handle(error, 'ArduinoCollector.collect');
            return {
                success: false,
                devicesFound: 0,
                devicesSpoofed: 0,
                hostShieldHidden: false,
                mouseControllerReady: false,
                collectionDuration: 0,
                errors: [error.message]
            };
        }
    }

    /**
     * Perform automatic spoofing of detected Arduino and USB Host Shield devices
     * @param {Array} devices - Detected devices
     * @returns {Promise<Object>} Spoofing results
     */
    async performAutoSpoofing(devices) {
        const results = {
            spoofedCount: 0,
            spoofedDevices: [],
            errors: []
        };

        // Priority devices for spoofing
        const priorityDevices = devices.filter(device => 
            device.type === 'usb_host_shield' || device.type === 'arduino'
        );

        // Also spoof HID devices that might be suspicious
        const hidDevices = devices.filter(device => 
            device.type === 'hid_device' && device.name.toLowerCase().includes('arduino')
        );

        const devicesToSpoof = [...priorityDevices, ...hidDevices];

        logger.info(`Auto-spoofing ${devicesToSpoof.length} devices`, {
            deviceTypes: devicesToSpoof.map(d => d.type)
        });

        for (const device of devicesToSpoof) {
            try {
                // eslint-disable-next-line no-await-in-loop
                const spoofSuccess = await this.spoofer.spoofDevice(device.id);
                if (spoofSuccess) {
                    results.spoofedCount++;
                    results.spoofedDevices.push({
                        id: device.id,
                        name: device.name,
                        type: device.type
                    });

                    this.addOperationLog('spoof_device', {
                        deviceId: device.id,
                        deviceName: device.name,
                        deviceType: device.type,
                        success: true
                    });
                } else {
                    this.addOperationLog('spoof_device', {
                        deviceId: device.id,
                        deviceName: device.name,
                        deviceType: device.type,
                        success: false,
                        error: 'Spoofing failed'
                    });
                }
            } catch (error) {
                results.errors.push(`Failed to spoof device ${device.id}: ${error.message}`);
                this.addOperationLog('spoof_device', {
                    deviceId: device.id,
                    deviceName: device.name,
                    deviceType: device.type,
                    success: false,
                    error: error.message
                });
            }
        }

        return results;
    }

    /**
     * Demonstrate mouse control capabilities
     * @returns {Promise<void>}
     */
    async demonstrateMouseControl() {
        try {
            logger.info('Demonstrating mouse control via USB Host Shield');

            // Small mouse movements to test functionality
            const movements = [
                { x: 10, y: 0 },
                { x: 0, y: 10 },
                { x: -10, y: 0 },
                { x: 0, y: -10 }
            ];

            for (const movement of movements) {
                // eslint-disable-next-line no-await-in-loop
                await this.spoofer.moveMouse(movement.x, movement.y);
                // eslint-disable-next-line no-await-in-loop
                await this.sleep(100); // Small delay between movements
            }

            // Test click functionality
            await this.spoofer.clickMouse('left', true);
            await this.sleep(50);
            await this.spoofer.clickMouse('left', false);

            this.addOperationLog('mouse_control_demo', {
                movements: movements.length,
                clicksPerformed: 1,
                success: true
            });

            logger.info('Mouse control demonstration completed successfully');
        } catch (error) {
            logger.warn('Mouse control demonstration failed:', error.message);
            this.addOperationLog('mouse_control_demo', {
                success: false,
                error: error.message
            });
        }
    }

    /**
     * Save collected Arduino data to files
     * @returns {Promise<void>}
     */
    async saveCollectionData() {
        try {
            // Save device enumeration data
            const devicesReport = this.generateDevicesReport();
            await fileManager.saveTextAsync(
                devicesReport, 
                'Arduino', 
                'devices.txt'
            );

            // Save spoofing status
            const spoofingReport = this.generateSpoofingReport();
            await fileManager.saveTextAsync(
                spoofingReport, 
                'Arduino', 
                'spoofing_status.txt'
            );

            // Save operation logs
            const operationLogs = this.generateOperationLogsReport();
            await fileManager.saveTextAsync(
                operationLogs, 
                'Arduino', 
                'operation_logs.txt'
            );

            // Save raw data as JSON
            await fileManager.saveJsonAsync(
                this.collectedData, 
                'Arduino', 
                'raw_data.json'
            );

            logger.debug('Arduino collection data saved successfully');
        } catch (error) {
            logger.warn('Failed to save Arduino collection data:', error.message);
        }
    }

    /**
     * Generate human-readable devices report
     * @returns {string} Formatted devices report
     */
    generateDevicesReport() {
        const devices = this.collectedData.devices;
        let report = `=== ARDUINO AND USB DEVICES (${devices.length} entries) ===\n\n`;

        devices.forEach((device, index) => {
            report += `[${index + 1}] ${device.name}\n`;
            report += `Device ID: ${device.id}\n`;
            report += `Type: ${device.type}\n`;
            report += `Description: ${device.description}\n`;
            report += `Platform: ${device.platform}\n`;
            
            if (device.bus) {
                report += `Bus: ${device.bus}\n`;
            }
            if (device.device) {
                report += `Device Number: ${device.device}\n`;
            }

            const spoofed = this.spoofer?.spoofedDevices.has(device.id);
            report += `Spoofed: ${spoofed ? 'Yes' : 'No'}\n`;
            
            report += '==================================================\n\n';
        });

        return report;
    }

    /**
     * Generate spoofing status report
     * @returns {string} Formatted spoofing status
     */
    generateSpoofingReport() {
        const status = this.collectedData.spoofingStatus;
        let report = '=== ARDUINO SPOOFING STATUS ===\n\n';

        report += `Total Devices Found: ${status.totalDevices}\n`;
        report += `Devices Spoofed: ${status.spoofedDevices}\n`;
        report += `USB Host Shield Hidden: ${status.hostShieldHidden ? 'Yes' : 'No'}\n`;
        report += `Mouse Controller Ready: ${status.mouseControllerReady ? 'Yes' : 'No'}\n`;
        report += `Platform: ${status.platform}\n\n`;

        if (status.spoofedDeviceDetails && status.spoofedDeviceDetails.length > 0) {
            report += '=== SPOOFED DEVICES DETAILS ===\n\n';
            status.spoofedDeviceDetails.forEach((device, index) => {
                report += `[${index + 1}] Original ID: ${device.originalId}\n`;
                report += `Spoofed ID: ${device.spoofedId}\n`;
                report += `Spoofed Name: ${device.spoofedName}\n`;
                report += `Duration: ${Math.round(device.spoofingDuration / 1000)}s\n`;
                report += '==================================================\n\n';
            });
        }

        return report;
    }

    /**
     * Generate operation logs report
     * @returns {string} Formatted operation logs
     */
    generateOperationLogsReport() {
        const logs = this.collectedData.operationLogs;
        let report = `=== ARDUINO OPERATION LOGS (${logs.length} entries) ===\n\n`;

        logs.forEach((log, index) => {
            report += `[${index + 1}] ${log.timestamp}\n`;
            report += `Operation: ${log.operation}\n`;
            report += `Success: ${log.data.success ? 'Yes' : 'No'}\n`;
            
            if (log.data.deviceId) {
                report += `Device ID: ${log.data.deviceId}\n`;
            }
            if (log.data.deviceName) {
                report += `Device Name: ${log.data.deviceName}\n`;
            }
            if (log.data.error) {
                report += `Error: ${log.data.error}\n`;
            }
            
            report += '==================================================\n\n';
        });

        return report;
    }

    /**
     * Add operation log entry
     * @param {string} operation - Operation name
     * @param {Object} data - Operation data
     */
    addOperationLog(operation, data) {
        this.collectedData.operationLogs.push({
            timestamp: new Date().toISOString(),
            operation,
            data
        });
    }

    /**
     * Sleep for specified milliseconds
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise<void>}
     */
    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Get collected data summary
     * @returns {Object} Data summary
     */
    getDataSummary() {
        return {
            devicesCount: this.collectedData.devices.length,
            spoofedDevicesCount: this.collectedData.spoofingStatus.spoofedDevices || 0,
            hostShieldHidden: this.collectedData.spoofingStatus.hostShieldHidden || false,
            mouseControllerReady: this.collectedData.spoofingStatus.mouseControllerReady || false,
            operationLogsCount: this.collectedData.operationLogs.length
        };
    }

    /**
     * Cleanup Arduino collector
     */
    async cleanup() {
        try {
            logger.info('Cleaning up Arduino collector');

            if (this.spoofer) {
                await this.spoofer.cleanup();
            }

            this.collectedData = {
                devices: [],
                spoofingStatus: {},
                mouseControllerInfo: {},
                operationLogs: []
            };

            logger.info('Arduino collector cleanup completed');
        } catch (error) {
            logger.error('Arduino collector cleanup failed:', error.message);
            ErrorHandler.handle(error, 'ArduinoCollector.cleanup');
        }
    }
}

module.exports = {
    ArduinoCollector
};