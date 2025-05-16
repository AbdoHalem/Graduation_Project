#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include "radialbar.h"
#include "bluetoothhandler.h" // Include Bluetooth handler

int main(int argc, char *argv[])
{
#if QT_VERSION < QT_VERSION_CHECK(6, 0, 0)
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
#endif

    QGuiApplication app(argc, argv);

    QQmlApplicationEngine engine;

    // Register RadialBar for QML
    qmlRegisterType<RadialBar>("CustomControls", 1, 0, "RadialBar");

    // Create and expose Bluetooth handler
    BluetoothHandler btHandler;
    engine.rootContext()->setContextProperty("btHandler", &btHandler);

    const QUrl url(QStringLiteral("qrc:/main.qml"));
    QObject::connect(&engine, &QQmlApplicationEngine::objectCreated,
                     &app, [url](QObject *obj, const QUrl &objUrl) {
                         if (!obj && url == objUrl)
                             QCoreApplication::exit(-1);
                     }, Qt::QueuedConnection);

    engine.load(url);

    return app.exec();
}
