#include <QtTest/QtTest>

class TestError: public QObject
{
    Q_OBJECT
private slots:
    void testErrorOne();
    void testErrorTwo();
};

void TestError::testErrorOne()
{
    throw std::runtime_error("unexpected exception");
}

void TestError::testErrorTwo()
{
    throw std::runtime_error("another unexpected exception");
}

QTEST_MAIN(TestError)
#include "qt_error.moc"
