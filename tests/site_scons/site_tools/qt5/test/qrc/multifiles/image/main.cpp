#include <QtWidgets/QApplication>
#include <QtCore>

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);

    Q_INIT_RESOURCE(icons);
    Q_INIT_RESOURCE(other);

    return 0;
}
