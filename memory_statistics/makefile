# Required variables:
# SRCS: source files to measure
# CFLAGS: Flags nessesary, such as include directories

CC=arm-none-eabi-gcc
override CFLAGS+=-std=gnu99 -ggdb -DNDEBUG
override CFLAGS+=-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16

OBJS=$(SRCS:.c=.o)

.PHONY: size clean

size: $(OBJS)
	arm-none-eabi-size -B $(OBJS)

clean:
	rm -rf $(OBJS)
