#ifndef BLUETOOTHHANDLER_H
#define BLUETOOTHHANDLER_H

#include <QObject>
#include <QBluetoothSocket>
#include <QBluetoothAddress>
#include <QBluetoothUuid>
#include <QTimer>

class BluetoothHandler : public QObject
{
    Q_OBJECT
public:
    explicit BluetoothHandler(QObject *parent = nullptr);

    // Optional: to be triggered automatically
    Q_INVOKABLE void start();

    Q_INVOKABLE void connectToESP32(const QString &macAddress);
    Q_INVOKABLE void sendMessage(const QString &message);


private slots:
    void onConnected();
    void onDisconnected();
    void onError(QBluetoothSocket::SocketError error);

private:
    QBluetoothSocket *socket = nullptr;
   QString defaultMacAddress = "EC:62:6O:76:6A:C6";
   // QString defaultMacAddress = "cc:db:a7:02:fb:cc";    // Replace with your ESP32 MAC
};

#endif // BLUETOOTHHANDLER_H
