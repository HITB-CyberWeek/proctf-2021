import asyncio
import client

async def main():
    c = client.Client('127.0.0.1', 12345)
    await c.connect()
    mid = await c.upload([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], 'desc', 'key')
    print('id:', mid)

    print()

    matrix, desc = await c.download(mid, 'key')
    print('matrix:', matrix)
    print('desc:', desc)

    print()

    matrix = await c.convolution(mid, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    print('matrix: ', matrix)

    print()

    matrix = await c.convolution(mid, [[0], [1]])
    print('matrix: ', matrix)

    print()

    matrix = await c.convolution(mid, [[0, 0, 1]])
    print('matrix: ', matrix)

    print()

    try:
        matrix, desc = await c.download(mid, 'key1')
        print('matrix:', matrix)
        print('desc:', desc)
    except Exception as ex:
        print(ex)

    await c.close()

if __name__ == '__main__':
    asyncio.run(main())

