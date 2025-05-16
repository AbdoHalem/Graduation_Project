#include "bluetoothhandler.h"
#include <QDebug>
#include <QTimer>

BluetoothHandler::BluetoothHandler(QObject *parent) : QObject(parent)
{
    socket = new QBluetoothSocket(QBluetoothServiceInfo::RfcommProtocol, this);

    connect(socket, &QBluetoothSocket::connected, this, &BluetoothHandler::onConnected);
    connect(socket, &QBluetoothSocket::disconnected, this, &BluetoothHandler::onDisconnected);
    connect(socket, QOverload<QBluetoothSocket::SocketError>::of(&QBluetoothSocket::error),
            this, &BluetoothHandler::onError);

    // Automatically start after short delay
    QTimer::singleShot(2000, this, &BluetoothHandler::start);
}

void BluetoothHandler::start()
{
    connectToESP32(defaultMacAddress);
}

void BluetoothHandler::connectToESP32(const QString &macAddress)
{
    if (socket->state() == QBluetoothSocket::ConnectedState) {
        qDebug() << "Already connected.";
        return;
    }

    QBluetoothAddress address(macAddress);
    QBluetoothUuid uuid(QBluetoothUuid::SerialPort);

    qDebug() << "Attempting to connect to" << macAddress;

    socket->connectToService(address, uuid);
}

void BluetoothHandler::sendMessage(const QString &message)
{
    if (socket && socket->isOpen()) {
        QString fullMessage = message + "\n";  // Ensure newline
        socket->write(fullMessage.toUtf8());
        //socket->flush(); // Optional, ensures buffer is sent
        qDebug() << "Sent:" << fullMessage;
    } else {
        qDebug() << "Socket not open";
    }
}




void BluetoothHandler::onConnected()
{
    qDebug() << "Connected to ESP32.";
    sendMessage("Hello ESP32 from elfeky");
}

void BluetoothHandler::onDisconnected()
{
    qDebug() << "Disconnected from ESP32";
}

void BluetoothHandler::onError(QBluetoothSocket::SocketError error)
{
    qWarning() << "Bluetooth error:" << error << socket->errorString();
}
