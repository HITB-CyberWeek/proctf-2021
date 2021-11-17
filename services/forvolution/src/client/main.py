import asyncio
import client

async def main():
    c = client.Client('127.0.0.1', 12345)
    await c.connect()
    mid = await c.upload([[1, 2], [3, 4]], 'desc', 'key')
    print('id:', mid)
    try:
        matrix, desc = await c.download(mid, 'key')
        print('matrix:', matrix)
        print('desc:', desc)
    except Exception as ex:
        print(ex)

    try:
        matrix, desc = await c.download(mid, 'key1')
        print('matrix:', matrix)
        print('desc:', desc)
    except Exception as ex:
        print(ex)

    matrix = await c.convolution(mid, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    print('matrix: ', matrix)

    matrix = await c.convolution(mid, [[1]] * 9)
    print('matrix: ', matrix)

    matrix = await c.convolution(mid, [[1] * 9])
    print('matrix: ', matrix)

    await c.close()

if __name__ == '__main__':
    asyncio.run(main())

