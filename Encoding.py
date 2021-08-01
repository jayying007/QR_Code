from reedsolo import RSCodec


def _fmtEncode(fmt):
    """Encode the 15-bit format code using BCH code."""
    g = 0x537
    code = fmt << 10
    for i in range(4, -1, -1):
        if code & (1 << (i + 10)):
            code ^= g << i
    return ((fmt << 10) ^ code) ^ 0b101010000010010


def _rsEncode(data, per_block_data, number_of_block, per_block_err):
    # Byte mode prefix 0100.
    bitstring = '0100'
    # Character count in 8 binary bits.
    bitstring += '{:08b}'.format(len(data))
    # Encode every character in ISO-8859-1 in 8 binary bits.
    for c in data:
        bitstring += '{:08b}'.format(ord(c.encode('iso-8859-1')))
    # Terminator 0000.
    bitstring += '0000'
    res = list()
    # Convert string to byte numbers.
    while bitstring:
        res.append(int(bitstring[:8], 2))
        bitstring = bitstring[8:]
    total_data_length = per_block_data * number_of_block
    # Add padding pattern.
    while len(res) < total_data_length:
        res.append(int('11101100', 2))
        res.append(int('00010001', 2))
    # Slice to 60 bytes for V6-H.
    res = res[:total_data_length]

    ecc = RSCodec(per_block_err)
    blocks = []
    for i in range(number_of_block):
        block = ecc.encode(res[:per_block_data])
        blocks.append(block)
        res = res[per_block_data:]
    # 先拼接数据，再拼接纠错编码
    final_res = ''
    # 如果使用其他版本，可能不同数据块长度不同，请注意，这里四个数据块长度都是43
    for i in range(per_block_data):
        for j in range(4):
            final_res = final_res + '{:08b}'.format(blocks[j][i])
    for i in range(per_block_data, per_block_data+per_block_err):
        for j in range(4):
            final_res = final_res + '{:08b}'.format(blocks[j][i])
    return final_res
