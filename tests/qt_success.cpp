#include <QtTest/QtTest>

class TestSuccess: public QObject
{
    Q_OBJECT
private slots:
    void testSuccessOne();
    void testSuccessTwo();
};

void TestSuccess::testSuccessOne()
{
    QCOMPARE(2 * 3, 6);
}

void TestSuccess::testSuccessTwo()
{
    QCOMPARE(3 * 4, 12);
}

QTEST_MAIN(TestSuccess)
#include "qt_success.moc"
